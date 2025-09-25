import hashlib
import random
import re
from typing import Optional, Dict, Any
import pandas as pd
import numpy as np

class DataTokenizer:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._setup_default_config()
        
    def _setup_default_config(self):
        defaults = {
            'name_list': ["Aarav","Vivaan","Kabir","Rohan","Arjun","Aditya","Vihaan","Ishaan",
                         "Reyansh","Atharv","Ananya","Ishita","Kavya","Riya","Sanya","Meera",
                         "Diya","Myra","Aadhya","Navya","Joe","Alex","Mack","Zara","Noah",
                         "Oliver","James","Liam","Emma","Olivia","Ava","Sophia","Isabella",
                         "Henry","Lucas","Leo","Max","Finn","Ethan","Ravi","Tashvi","Aarav",
                         "Aashi","Pooja","Pranav","Priyanshi","Priyansh","Piyush","Shorya"],
            'city_list': ["Mumbai","Delhi","Bengaluru","Hyderabad","Chennai","Pune","Kolkata",
                         "Jaipur","Ahmedabad","Lucknow","Surat","Indore","Bhopal","Nagpur",
                         "Noida","Visakhapatnam","Chandigarh","California","Texas","Florida",
                         "New York","Maryland","Colorado"],
            'mask_digits': 4,
            'token_prefixes': {
                'aadhaar': 'AAD',
                'ssn': 'SSN',
                'card': 'CARD',
                'receiver_card': 'RCARD'
            }
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def _salt_or_new(self, salt: Optional[str]) -> str:
        return salt if salt else hex(random.getrandbits(128))  # Increased to 128 bits for better security
    
    def _sha(self, val: str) -> str:
        return hashlib.sha256(val.encode()).hexdigest()
    
    def _token(self, prefix: str, raw: str, salt: str) -> str:
        return f"{prefix}-{self._sha(salt + '|' + str(raw))[:12]}"
    
    def _mask_keep_last(self, num: str, last: int = None) -> str:
        if last is None:
            last = self.config['mask_digits']
            
        s = "".join(ch for ch in str(num) if ch.isdigit())
        if len(s) <= last: 
            return s
        return "*" * (len(s) - last) + s[-last:]
    
    def _mask_keep_first_last(self, num: str, keep: int = 2) -> str:
        s = "".join(ch for ch in str(num) if ch.isdigit())
        if len(s) <= keep * 2: 
            return s
        return s[:keep] + "*" * (len(s) - keep * 2) + s[-keep:]
    
    def _city_from_hash(self, text: str, salt: str) -> str:
        h = int(self._sha(salt + "|" + text), 16)
        return self.config['city_list'][h % len(self.config['city_list'])]
    
    def _name_from_hash(self, text: str, salt: str) -> str:
        h = int(self._sha(salt + "|" + text), 16)
        return self.config['name_list'][h % len(self.config['name_list'])]
    
    def _email_from_hash(self, text: str, salt: str, domain: str = "example.com") -> str:
        name_part = self._name_from_hash(text, salt + "|email").lower().replace(" ", ".")
        return f"{name_part}@{domain}"
    
    def tokenize_dataset(self, df: pd.DataFrame, salt: Optional[str] = None) -> pd.DataFrame:
        salt = self._salt_or_new(salt)
        out = df.copy()
        
        # Create a mapping of column patterns to transformation functions
        transformation_map = [
            # Names
            (lambda c: "name" in c.lower() and "transaction" not in c.lower() and "location" not in c.lower(),
             lambda v, c: self._name_from_hash(str(v), salt + "|" + c)),
            
            # Aadhaar numbers
            (lambda c: "aadhaar" in c.lower() or "aadhar" in c.lower(),
             lambda v, c: self._token(self.config['token_prefixes']['aadhaar'], v, salt)),
            
            # SSN numbers
            (lambda c: c.lower() == "ssn" or "ssn" in c.lower(),
             lambda v, c: self._token(self.config['token_prefixes']['ssn'], v, salt)),
            
            # Card numbers (receiver)
            (lambda c: "card" in c.lower() and "receiver" in c.lower(),
             lambda v, c: self._token(self.config['token_prefixes']['receiver_card'], v, salt)),
            
            # Card numbers (general)
            (lambda c: "card" in c.lower(),
             lambda v, c: self._token(self.config['token_prefixes']['card'], v, salt)),
            
            # Phone numbers
            (lambda c: "phone" in c.lower() or "mobile" in c.lower(),
             lambda v, c: self._mask_keep_last(str(v))),
            
            # Email addresses
            (lambda c: "email" in c.lower(),
             lambda v, c: self._email_from_hash(str(v), salt + "|" + c)),
            
            # Addresses
            (lambda c: "address" in c.lower(),
             lambda v, c: self._city_from_hash(str(v), salt + "|" + c)),
        ]
        
        # Apply transformations
        for col in out.columns:
            for condition, transform in transformation_map:
                if condition(col):
                    try:
                        out[col] = out[col].astype(str).apply(lambda v: transform(v, col))
                        break  # Move to next column after applying transformation
                    except Exception as e:
                        print(f"Error processing column {col}: {e}")
                        # Keep original values if transformation fails
        
        return out

# Global function for backward compatibility
def tokenize_dataset(df: pd.DataFrame, salt: Optional[str] = None) -> pd.DataFrame:
    tokenizer = DataTokenizer()
    return tokenizer.tokenize_dataset(df, salt)

if __name__ == "__main__":
    df = pd.read_csv("input_real.csv")
    tok = tokenize_dataset(df)
    tok.to_csv("tokenized_output.csv", index=False)
    print("✅ tokenized_output.csv written")