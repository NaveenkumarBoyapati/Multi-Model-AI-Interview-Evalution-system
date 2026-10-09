import os

for f in ["'", "{clist}')"]:
    p = os.path.join(r"d:\Nani Personal\multi model another work", f)
    if os.path.exists(p):
        os.remove(p)
        print("Removed", f)
