import pytest

from app.services.crypto import decrypt, encrypt, generate_encryption_key, is_encrypted


class TestGenerateEncryptionKey:
    def test_generates_valid_base64(self):
        import base64
        key = generate_encryption_key()
        decoded = base64.urlsafe_b64decode(key)
        assert len(decoded) == 32

    def test_generates_unique_keys(self):
        key1 = generate_encryption_key()
        key2 = generate_encryption_key()
        assert key1 != key2


class TestEncryptDecrypt:
    def test_round_trip(self):
        key = generate_encryption_key()
        plaintext = b"hello world 12345"
        encrypted = encrypt(plaintext, key)
        assert encrypted != plaintext
        assert is_encrypted(encrypted)
        decrypted = decrypt(encrypted, key)
        assert decrypted == plaintext

    def test_encrypted_has_version_prefix(self):
        key = generate_encryption_key()
        encrypted = encrypt(b"data", key)
        assert encrypted[0] == 0x01

    def test_different_nonce_each_time(self):
        key = generate_encryption_key()
        plaintext = b"same data"
        e1 = encrypt(plaintext, key)
        e2 = encrypt(plaintext, key)
        assert e1 != e2
        assert decrypt(e1, key) == plaintext
        assert decrypt(e2, key) == plaintext

    def test_wrong_key_fails(self):
        key1 = generate_encryption_key()
        key2 = generate_encryption_key()
        encrypted = encrypt(b"secret", key1)
        with pytest.raises(Exception):
            decrypt(encrypted, key2)

    def test_tampered_data_fails(self):
        key = generate_encryption_key()
        encrypted = encrypt(b"secret", key)
        tampered = bytearray(encrypted)
        tampered[-1] ^= 0xFF
        with pytest.raises(Exception):
            decrypt(bytes(tampered), key)

    def test_is_encrypted_false_for_plaintext(self):
        assert is_encrypted(b"") is False
        assert is_encrypted(b"\x00hello") is False
        assert is_encrypted(b"\x01nonceciphertext") is True

    def test_encrypt_decrypt_large_data(self):
        key = generate_encryption_key()
        plaintext = b"\x00" * 2048
        encrypted = encrypt(plaintext, key)
        decrypted = decrypt(encrypted, key)
        assert decrypted == plaintext


class TestIsEncrypted:
    def test_empty_bytes(self):
        assert is_encrypted(b"") is False

    def test_unencrypted_prefix(self):
        assert is_encrypted(b"\x02data") is False

    def test_encrypted_prefix(self):
        key = generate_encryption_key()
        encrypted = encrypt(b"data", key)
        assert is_encrypted(encrypted) is True