from ben10.foundation.is_frozen import IsDevelopment, IsFrozen, SetIsDevelopment, SetIsFrozen



def testIsFrozenIsDevelopment():
    assert IsFrozen() == False
    assert IsDevelopment() == True

    SetIsDevelopment(False)
    assert IsFrozen() == False
    assert IsDevelopment() == False

    SetIsDevelopment(True)
    assert IsFrozen() == False
    assert IsDevelopment() == True

    SetIsFrozen(True)
    assert IsFrozen() == True
    assert IsDevelopment() == True

    SetIsFrozen(False)
    assert IsFrozen() == False
    assert IsDevelopment() == True
