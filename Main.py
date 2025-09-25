import hashlib
import random
from typing import Optional, Dict, Any, List, Tuple
import pandas as pd
import numpy as np
from datetime import date, datetime, timedelta
from faker import Faker  # for fake names, emails, etc.

class SyntheticDataGenerator:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._setup_default_config()
        self.faker = Faker()
        
    def _setup_default_config(self):
        defaults = {
            'names': {
                'male': ["Aarav", "Vivaan", "Kabir", "Rohan", "Arjun", "Aditya", "Vihaan", 
                        "Ishaan", "Reyansh", "Atharv", "Noah", "Oliver", "James", "Liam", 
                        "Henry", "Lucas", "Leo", "Max", "Finn", "Ethan", "Ravi", "Pranav",
                        "Priyansh", "Piyush"],
                'female': ["Ananya", "Ishita", "Kavya", "Riya", "Sanya", "Meera", "Diya", 
                          "Myra", "Aadhya", "Navya", "Zara", "Emma", "Olivia", "Ava", 
                          "Sophia", "Isabella", "Aashi", "Pooja", "Priyanshi", "Tashvi"]
            },
            'cities': ["Mumbai", "Delhi", "Bengaluru", "Hyderabad", "Chennai", "Pune", 
                      "Kolkata", "Jaipur", "Ahmedabad", "Lucknow", "Surat", "Indore", 
                      "Bhopal", "Nagpur", "Noida", "Visakhapatnam", "Chandigarh"],
            'isps': ["Jio", "Airtel", "BSNL", "Vodafone", "ACT", "Hathway", "Verizon", 
                    "T-Mobile", "AT&T", "Spectrum", "Comcast"],
            'card_brands': {
                "visa": "4",
                "mastercard": "5", 
                "amex": "3"
            },
            'amount_ranges': {
                "TransactionAmount": (0.6, 1.7, 50.0),
                "SenderBankBalance": (0.8, 1.3, 100.0),
                "ReceiverBankBalance": (0.8, 1.3, 100.0),
                "SenderAnnualIncome": (0.85, 1.25, 50000.0),
                "ReceiverAnnualIncome": (0.85, 1.25, 50000.0),
            },
            'fraud_indicators': {
                'high_amount_threshold': 8000,
                'high_amount_risk_increase': 0.25,
                'new_account_risk_increase': 0.15,
                'base_fraud_probability': 0.1,
                'max_fraud_probability': 0.9
            }
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def _rng(self, salt: str, key: str) -> random.Random:
        seed = int(hashlib.sha256((salt + "|" + key).encode()).hexdigest(), 16) % (2**32)
        return random.Random(seed)
    
    def _hashint(self, salt: str, key: str) -> int:
        return int(hashlib.sha256((salt + "|" + key).encode()).hexdigest(), 16)
    
    def _det_name(self, salt: str, key: str, gender: Optional[str] = None) -> str:
        r = self._hashint(salt, "name|" + key)
        
        if gender and gender.lower() in ['male', 'm']:
            name_list = self.config['names']['male']
        elif gender and gender.lower() in ['female', 'f']:
            name_list = self.config['names']['female']
        else:
           # fallback: use all names
            name_list = self.config['names']['male'] + self.config['names']['female']
            
        return name_list[r % len(name_list)]
    
    def _det_city(self, salt: str, key: str) -> str:
        r = self._hashint(salt, "city|" + key)
        return self.config['cities'][r % len(self.config['cities'])]
    
    def _det_ip(self, salt: str, key: str) -> str:
        r = self._rng(salt, "ip|" + key)
        return f"{r.randint(1,223)}.{r.randint(0,255)}.{r.randint(0,255)}.{r.randint(1,254)}"
    
    def _det_isp(self, salt: str, key: str) -> str:
        r = self._hashint(salt, "isp|" + key)
        return self.config['isps'][r % len(self.config['isps'])]
    
    def _det_date_young(self, salt: str, key: str, min_age: int = 18, max_age: int = 70) -> str:
        r = self._rng(salt, "dob|" + key)
        age = r.randint(min_age, max_age)
        year = date.today().year - age
        month = r.randint(1, 12)
        day = r.randint(1, 28)
        return f"{year:04d}-{month:02d}-{day:02d}"
    
    def _det_date_recent(self, salt: str, key: str, years: int = 10) -> str:
        r = self._rng(salt, "recent|" + key)
        year = date.today().year - r.randint(0, years)
        month = r.randint(1, 12)
        day = r.randint(1, 28)
        return f"{year:04d}-{month:02d}-{day:02d}"
    
    def _det_time(self, salt: str, key: str) -> str:
        r = self._rng(salt, "time|" + key)
        return f"{r.randint(0,23):02d}:{r.randint(0,59):02d}:{r.randint(0,59):02d}"
    
    def _luhn_checkdigit(self, num15: str) -> str:
        digits = [int(x) for x in num15]
        for i in range(len(digits)-1, -1, -2):
            doubled = digits[i]*2
            digits[i] = doubled - 9 if doubled > 9 else doubled
        s = sum(digits)
        return str((10 - (s % 10)) % 10)
    
    def _det_card(self, salt: str, key: str, brand: str = "visa") -> str:
        if brand not in self.config['card_brands']:
            brand = "visa"  # default
            
        prefix = self.config['card_brands'][brand]
        base = f"{prefix}{str(self._hashint(salt, 'card|' + key))[:15-len(prefix)]}".zfill(15)
        return base + self._luhn_checkdigit(base)
    
    def _det_digits(self, salt: str, key: str, n: int) -> str:
        return (str(self._hashint(salt, "digits|" + key)))[-n:].zfill(n)
    
    def _perturb(self, val, salt: str, key: str, low: float, high: float, floor: float) -> float:
        try:
            x = float(val)
        except (ValueError, TypeError):
            return val
            
        r = self._rng(salt, "noise|" + key)
        factor = r.uniform(low, high)
        return round(max(floor, x * factor), 2)
    
    def _first_nonempty(self, row, candidates) -> str:
        for c in candidates:
            if c in row and pd.notna(row[c]) and str(row[c]).strip() != "":
                return str(row[c])
        return ""
    
    def _detect_column_types(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """Automatically detect column types based on name patterns"""
        column_categories = {
            'name_columns': [],
            'address_columns': [],
            'id_columns': [],
            'date_columns': [],
            'amount_columns': [],
            'phone_columns': [],
            'email_columns': [],
            'ip_columns': [],
            'gender_columns': []
        }
        
        for col in df.columns:
            col_lower = col.lower()
            
            if any(x in col_lower for x in ['name', 'firstname', 'lastname']):
                column_categories['name_columns'].append(col)
            elif any(x in col_lower for x in ['address', 'city', 'location']):
                column_categories['address_columns'].append(col)
            elif any(x in col_lower for x in ['id', 'ssn', 'aadhaar', 'aadhar', 'pan']):
                column_categories['id_columns'].append(col)
            elif any(x in col_lower for x in ['date', 'time', 'dob', 'birth']):
                column_categories['date_columns'].append(col)
            elif any(x in col_lower for x in ['amount', 'balance', 'income', 'price', 'value']):
                column_categories['amount_columns'].append(col)
            elif any(x in col_lower for x in ['phone', 'mobile', 'contact']):
                column_categories['phone_columns'].append(col)
            elif 'email' in col_lower:
                column_categories['email_columns'].append(col)
            elif 'ip' in col_lower:
                column_categories['ip_columns'].append(col)
            elif 'gender' in col_lower:
                column_categories['gender_columns'].append(col)
                
        return column_categories
    
    def generate_synthetic_data(self, df: pd.DataFrame, salt: Optional[str] = None) -> pd.DataFrame:
        salt = salt if salt else hex(random.getrandbits(128))
        out_rows = []
        
        column_types = self._detect_column_types(df)
        
        for i, row in df.iterrows():
            sender_key = self._first_nonempty(row, ["SenderAadhar", "SenderSSN", "SenderPhone", "SenderName"]) or f"snd{i}"
            receiver_key = self._first_nonempty(row, ["ReceiverSSN", "ReceiverCard", "ReceiverPhone", "ReceiverName"]) or f"rcv{i}"
            txn_key = str(row.get("TransactionID", i))
            
            new = row.copy()
            
            # Names
            for col in column_types['name_columns']:
                base_key = sender_key if "receiver" not in col.lower() else receiver_key
                gender = None
                
                # Try to get gender if available
                if "sender" in col.lower() and "SenderGender" in df.columns:
                    gender = row.get("SenderGender")
                elif "receiver" in col.lower() and "ReceiverGender" in df.columns:
                    gender = row.get("ReceiverGender")
                    
                new[col] = self._det_name(salt, base_key + "|" + col, gender)
            
            # Address
            for col in column_types['address_columns']:
                base_key = sender_key if "receiver" not in col.lower() else receiver_key
                new[col] = self._det_city(salt, base_key + "|" + col)
            
            # IDs
            if "SenderAadhar" in df.columns:
                new["SenderAadhar"] = self._det_digits(salt, sender_key + "|aadhaar", 12)
            if "SenderSSN" in df.columns:
                new["SenderSSN"] = self._det_digits(salt, sender_key + "|ssn", 9)
            if "ReceiverSSN" in df.columns:
                new["ReceiverSSN"] = self._det_digits(salt, receiver_key + "|ssn", 9)
            
            # Cards
            if "SenderCard" in df.columns:
                new["SenderCard"] = self._det_card(salt, sender_key, "visa")
            if "ReceiverCard" in df.columns:
                new["ReceiverCard"] = self._det_card(salt, receiver_key, "mc")
            
            # IPs
            for col in column_types['ip_columns']:
                base_key = sender_key if "receiver" not in col.lower() else receiver_key
                new[col] = self._det_ip(salt, base_key + "|" + col)
            
            # ISPs
            for col in [c for c in df.columns if "isp" in c.lower()]:
                base_key = sender_key if "receiver" not in col.lower() else receiver_key
                new[col] = self._det_isp(salt, base_key + "|" + col)
            
            # Gender
            for col in column_types['gender_columns']:
                base_key = sender_key if "receiver" not in col.lower() else receiver_key
                r = self._rng(salt, "gender|" + base_key)
                new[col] = r.choice(["Male", "Female", "Other"])
            
            # Dates
            if "SenderDOB" in df.columns:
                new["SenderDOB"] = self._det_date_young(salt, sender_key)
            if "ReceiverDOB" in df.columns:
                new["ReceiverDOB"] = self._det_date_young(salt, receiver_key)
            if "TransactionDate" in df.columns:
                new["TransactionDate"] = self._det_date_recent(salt, txn_key, years=9)
            if "TransactionTime" in df.columns:
                new["TransactionTime"] = self._det_time(salt, txn_key)
            if "ReceiverAccountCreationDate" in df.columns:
                new["ReceiverAccountCreationDate"] = self._det_date_recent(salt, receiver_key, years=10)
            if "LastTransactionDate" in df.columns:
                new["LastTransactionDate"] = self._det_date_recent(salt, sender_key, years=2)
            
            # Process Amount columns with perturbation
            for col, params in self.config['amount_ranges'].items():
                if col in df.columns:
                    low, high, floor = params
                    new[col] = self._perturb(row[col], salt, txn_key + "|" + col, low, high, floor)
            
            # Generate fraud indicator if column exists
            if "Fraud" in df.columns:
                r = self._rng(salt, "fraud|" + txn_key)
                amt = float(new.get("TransactionAmount", 0) or 0)
                
                fraud_config = self.config['fraud_indicators']
                prob = fraud_config['base_fraud_probability']
                
                # High amount = fraud probability increases 
                if amt > fraud_config['high_amount_threshold']:
                    prob += fraud_config['high_amount_risk_increase']
                
                # New account = fraud probability increases
                if "ReceiverAccountCreationDate" in new:
                    creation_year = int(new["ReceiverAccountCreationDate"][:4])
                    if creation_year >= date.today().year - 1:
                        prob += fraud_config['new_account_risk_increase']
                
                new["Fraud"] = 1 if r.random() < min(prob, fraud_config['max_fraud_probability']) else 0
            
            out_rows.append(new)
        
        return pd.DataFrame(out_rows)

# wrapper for compatibility
def generate_synthetic_data(df: pd.DataFrame, salt: Optional[str] = None) -> pd.DataFrame:
    generator = SyntheticDataGenerator()
    return generator.generate_synthetic_data(df, salt)

if __name__ == "__main__":
    df = pd.read_csv("input_real.csv")
    syn = generate_synthetic_data(df)
    syn.to_csv("synthetic_output.csv", index=False)

    print("✅ synthetic_output.csv written")
