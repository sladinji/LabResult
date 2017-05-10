import hashlib
sel = '6699a7cbd81c468db76bdd89c7f6361e'

def hashpass(pw):
    return hashlib.sha512((pw + sel).encode("utf-8")).hexdigest()
