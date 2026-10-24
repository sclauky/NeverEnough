from app.core.security import hash_password, verify_password


def test_password_is_hashed():
    password = "MotDePasse-De-Test-123!"
    password_hash = hash_password(password)

    assert password_hash != password
    assert password_hash.startswith("$argon2id$")


def test_correct_password_is_verified():
    password = "MotDePasse-De-Test-123!"
    password_hash = hash_password(password)

    assert verify_password(password, password_hash) is True


def test_incorrect_password_is_rejected():
    password_hash = hash_password("MotDePasse-De-Test-123!")

    assert verify_password("MauvaisMotDePasse", password_hash) is False


def test_same_password_produces_different_hashes():
    password = "MotDePasse-De-Test-123!"

    first_hash = hash_password(password)
    second_hash = hash_password(password)

    assert first_hash != second_hash
    assert verify_password(password, first_hash)
    assert verify_password(password, second_hash)