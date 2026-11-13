"""Balanced radial constant-PQ AC power flow and independent nodal-equation solver."""
from pathlib import Path
from collections import deque
import re
import numpy as np
from scipy.optimize import root

def load_case(path):
    text=Path(path).read_text()
    def matrix(name):
        m=re.search(r'mpc\.'+name+r'\s*=\s*\[(.*?)\];',text,re.S)
        rows=[r.split('%')[0].strip().strip(';') for r in m.group(1).splitlines()]
        return np.array([[float(v) for v in r.split()] for r in rows if r])
    bus=matrix('bus'); branch=matrix('branch'); active=branch[branch[:,10]==1]
    base=float(re.search(r'mpc.baseMVA\s*=\s*([0-9.]+)',text)[1])
    n=len(bus); assert np.array_equal(bus[:,0],np.arange(1,n+1))
    assert len(active)==n-1 and (bus[:,4:6]==0).all() and (active[:,4]==0).all()
    assert np.isin(active[:,8],[0,1]).all() and (active[:,9]==0).all()
    zbase=bus[0,9]**2/base
    p=bus[:,2]/1000; q=bus[:,3]/1000
    z=(active[:,2]+1j*active[:,3])/zbase
    uv=active[:,:2].astype(int)-1
    adj=[[] for _ in range(n)];Y=np.zeros((n,n),complex)
    for (u,v),zz in zip(uv,z):
        adj[u].append((v,zz));adj[v].append((u,zz))
        yy=1/zz;Y[u,u]+=yy;Y[v,v]+=yy;Y[u,v]-=yy;Y[v,u]-=yy
    parent=np.full(n,-1,int);zp=np.zeros(n,complex);order=[0];seen={0};queue=deque([0])
    while queue:
        u=queue.popleft()
        for v,zz in adj[u]:
            if v not in seen:seen.add(v);parent[v]=u;zp[v]=zz;order.append(v);queue.append(v)
    assert len(seen)==n and int(bus[0,1])==3 and (bus[1:,1]==1).all()
    return {'name':Path(path).name,'n':n,'base':base,'p':p,'q':q,
            'parent':parent,'zp':zp,'order':np.array(order),'Y':Y,'uv':uv,'z':z}

def bfs(case,loads_MVA,tol=1e-12,maxiter=200):
    loads=np.atleast_2d(loads_MVA).astype(complex)
    S=loads/case['base'];T,n=S.shape
    V=np.ones((T,n),complex);parent=case['parent'];zp=case['zp'];order=case['order']
    last=np.full(T,np.inf);reached=np.zeros(T,int)
    with np.errstate(over='ignore',divide='ignore',invalid='ignore'):
        for iteration in range(1,maxiter+1):
            currents=np.conj(S/V);branch=currents.copy()
            for j in order[:0:-1]:branch[:,parent[j]]+=branch[:,j]
            new=np.ones_like(V)
            for j in order[1:]:new[:,j]=new[:,parent[j]]-zp[j]*branch[:,j]
            last=np.max(np.abs(new-V),axis=1)
            reached[(reached==0)&(last<tol)]=iteration
            V=new
            if np.all(last<tol):break
    uv=case['uv'];I=(V[:,uv[:,0]]-V[:,uv[:,1]])/case['z']
    loss=case['base']*1000*np.sum(np.abs(I)**2*case['z'].real,axis=1)
    injection=V*np.conj(V@case['Y'].T)
    residual=np.max(np.abs(injection[:,1:]+S[:,1:]),axis=1)
    balance=case['base']*1000*injection[:,0].real-loads.real.sum(1)*1000-loss
    ok=np.isfinite(V).all(1)&(last<tol)&(residual<1e-8)
    vm=np.abs(V)
    return {'V':V,'vm':vm,'vmin':vm[:,1:].min(1),'vmax':vm[:,1:].max(1),
            'loss_kW':loss,'residual_pu':residual,'balance_error_kW':balance,
            'ok':ok,'iterations':reached,'batch_iterations':iteration}

def ac_nodal_root(case,load_MVA):
    n=case['n'];S=np.asarray(load_MVA)/case['base'];Y=case['Y']
    def equations(x):
        V=np.r_[1+0j,x[:n-1]+1j*x[n-1:]]
        mismatch=(V*np.conj(Y@V)+S)[1:]
        return np.r_[mismatch.real,mismatch.imag]
    x0=np.r_[np.ones(n-1),np.zeros(n-1)]
    sol=root(equations,x0,method='hybr',options={'xtol':1e-11,'maxfev':5000})
    V=np.r_[1+0j,sol.x[:n-1]+1j*sol.x[n-1:]]
    residual=float(np.max(np.abs((V*np.conj(Y@V)+S)[1:])))
    return V,residual,sol

def make_loads(case,E_kWh,bus_ids,anchor_MW,alpha=.25,beta=.5,pf=1):
    E=np.atleast_2d(E_kWh)
    mapping=np.asarray(bus_ids,int)-1
    M=np.zeros((E.shape[1],case['n']))
    M[np.arange(E.shape[1]),mapping]=1
    c=alpha*case['p'].sum()/anchor_MW
    ev=(E/1000)@M*c
    qev=ev*np.tan(np.arccos(pf))
    return beta*(case['p']+1j*case['q'])[None,:]+ev+1j*qev
