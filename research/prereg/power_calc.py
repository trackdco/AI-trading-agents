"""Exact F-test power for the pre-registered joint test. No scipy available,
so the regularised incomplete beta is implemented directly (Numerical Recipes
continued fraction) and cross-checked against the df1=2 closed form."""
import math

def betacf(a, b, x, itmax=300, eps=3e-16):
    qab, qap, qam = a+b, a+1.0, a-1.0
    c = 1.0
    d = 1.0 - qab*x/qap
    if abs(d) < 1e-30: d = 1e-30
    d = 1.0/d; h = d
    for m in range(1, itmax+1):
        m2 = 2*m
        aa = m*(b-m)*x/((qam+m2)*(a+m2))
        d = 1.0 + aa*d
        if abs(d) < 1e-30: d = 1e-30
        c = 1.0 + aa/c
        if abs(c) < 1e-30: c = 1e-30
        d = 1.0/d; h *= d*c
        aa = -(a+m)*(qab+m)*x/((a+m2)*(qap+m2))
        d = 1.0 + aa*d
        if abs(d) < 1e-30: d = 1e-30
        c = 1.0 + aa/c
        if abs(c) < 1e-30: c = 1e-30
        d = 1.0/d; de = d*c; h *= de
        if abs(de-1.0) < eps: break
    return h

def betai(a, b, x):
    """Regularised incomplete beta I_x(a,b)."""
    if x <= 0.0: return 0.0
    if x >= 1.0: return 1.0
    bt = math.exp(math.lgamma(a+b) - math.lgamma(a) - math.lgamma(b)
                  + a*math.log(x) + b*math.log(1.0-x))
    if x < (a+1.0)/(a+b+2.0):
        return bt*betacf(a, b, x)/a
    return 1.0 - bt*betacf(b, a, 1.0-x)/b

def f_sf(f, d1, d2):
    """P(F(d1,d2) > f)."""
    if f <= 0: return 1.0
    return betai(d2/2.0, d1/2.0, d2/(d2 + d1*f))

def f_crit(alpha, d1, d2, lo=1e-6, hi=1e6):
    """Critical value: F such that P(F(d1,d2) > F) = alpha."""
    for _ in range(200):
        mid = math.sqrt(lo*hi)
        if f_sf(mid, d1, d2) > alpha: lo = mid
        else: hi = mid
    return math.sqrt(lo*hi)

def ncf_sf(f, d1, d2, lam):
    """P(noncentral F(d1,d2,lam) > f) via Poisson mixture over central F.
    kmax is scaled to cover the Poisson mode at lam/2 -- a fixed kmax silently
    returns ~0 for large lam, which makes power look monotonically wrong."""
    if lam == 0: return f_sf(f, d1, d2)
    m = lam/2.0
    kmax = int(m + 12*math.sqrt(m) + 80)
    tot = 0.0
    for k in range(kmax):
        logw = -m + k*math.log(m) - math.lgamma(k+1.0)
        if logw < -745: continue          # underflow guard, not a break
        tot += math.exp(logw) * f_sf(f*d1/(d1+2.0*k), d1+2.0*k, d2)
    return tot

def power(n, r2, d1, alpha):
    d2 = n - d1 - 1
    lam = n * (r2/(1.0-r2))          # Cohen f^2 * n
    return ncf_sf(f_crit(alpha, d1, d2), d1, d2, lam)

def n_for(r2, d1, alpha, target=0.80):
    lo, hi = d1+3, 100000
    if power(hi, r2, d1, alpha) < target: return None
    while lo < hi:
        mid = (lo+hi)//2
        if power(mid, r2, d1, alpha) < target: lo = mid+1
        else: hi = mid
    return lo

# ---- validation against known values -------------------------------------
print("VALIDATION")
print(f"  F(2,100) crit @0.05 = {f_crit(0.05,2,100):.4f}   (published 3.087)")
print(f"  F(2,1e7) crit @0.05 = {f_crit(0.05,2,1e7):.4f}   (chi2(2)/2 = {5.9915/2:.4f})")
print(f"  F(1,10)  crit @0.05 = {f_crit(0.05,1,10):.4f}   (published 4.965)")
cf = lambda a,nu: (nu/2.0)*(a**(-2.0/nu) - 1.0)   # closed form, d1=2
print(f"  closed-form d1=2 check: {cf(0.005,753):.4f} vs numeric {f_crit(0.005,2,753):.4f}")
print()

N = 756
print(f"PRE-REGISTERED DESIGN  n={N}")
for alpha,lab in [(0.05,'uncorrected'),(0.005,'Bonferroni L=10'),(0.0025,'Bonferroni L=20')]:
    fc = f_crit(alpha,2,N-3)
    print(f"\n  alpha={alpha:<7} ({lab})   F_crit(2,{N-3}) = {fc:.3f}")
    for r2 in (0.005,0.01,0.015,0.02,0.025,0.03,0.05):
        print(f"     R2={r2:5.3f}  power={power(N,r2,2,alpha):5.3f}   n for 80% power = {n_for(r2,2,alpha):6d}")

print("\n  Minimum detectable R2 at 80% power, alpha=0.005, n=756:")
lo,hi=0.0001,0.5
for _ in range(60):
    mid=(lo+hi)/2
    if power(N,mid,2,0.005)<0.80: lo=mid
    else: hi=mid
print(f"     R2_min = {(lo+hi)/2:.4f}  ({(lo+hi)/2*100:.2f}%)")

print("\n  Same, if release term is dropped (df1=1, beta1 only):")
lo,hi=0.0001,0.5
for _ in range(60):
    mid=(lo+hi)/2
    if power(N,mid,1,0.005)<0.80: lo=mid
    else: hi=mid
print(f"     R2_min = {(lo+hi)/2:.4f}  ({(lo+hi)/2*100:.2f}%)   F_crit={f_crit(0.005,1,N-2):.3f}")
