from passlib.context import CryptContext
import bcrypt

print(f"Bcrypt version: {bcrypt.__version__}")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
try:
    hashed = pwd_context.hash("password")
    print(f"Hash: {hashed}")
    verified = pwd_context.verify("password", hashed)
    print(f"Verify status: {verified}")
except Exception as e:
    print(f"Error during hashing: {e}")
    import traceback
    traceback.print_exc()
