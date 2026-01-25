import secrets
import string


def generate_password(
    length: int = 16,
    use_uppercase: bool = True,
    use_lowercase: bool = True,
    use_digits: bool = True,
    use_special: bool = True,
    exclude_chars: str = ''
) -> str:
    chars = ''
    
    if use_uppercase:
        chars += string.ascii_uppercase
    if use_lowercase:
        chars += string.ascii_lowercase
    if use_digits:
        chars += string.digits
    if use_special:
        chars += string.punctuation
    
    if exclude_chars:
        chars = ''.join(c for c in chars if c not in exclude_chars)
    
    if not chars:
        raise ValueError("Необходимо выбрать хотя бы один тип символов")
    
    return ''.join(secrets.choice(chars) for _ in range(length))
