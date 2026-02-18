"""
Specialist Data Loader
======================

Loads specialist/expert data from multiple sources:
- CSV File
- JSON File
- Database (SQLite/PostgreSQL)
- ServiceNow API
- Active Directory/LDAP

Configure the source in .env file using SPECIALIST_SOURCE variable.
"""

import os
import csv
import json
import logging
from typing import Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURATION
# ============================================================

# Source options: csv, json, database, servicenow, ldap, static
SPECIALIST_SOURCE = os.getenv("SPECIALIST_SOURCE", "static")

# File paths (for csv/json sources)
SPECIALISTS_CSV_PATH = os.getenv("SPECIALISTS_CSV_PATH", "data/specialists.csv")
SPECIALISTS_JSON_PATH = os.getenv("SPECIALISTS_JSON_PATH", "data/specialists.json")

# Database configuration
DB_TYPE = os.getenv("SPECIALISTS_DB_TYPE", "sqlite")  # sqlite, postgresql
DB_CONNECTION_STRING = os.getenv("SPECIALISTS_DB_CONNECTION", "data/specialists.db")

# Cache configuration (to avoid repeated API/DB calls)
CACHE_TTL_MINUTES = int(os.getenv("SPECIALISTS_CACHE_TTL", "15"))

# ============================================================
# CACHE
# ============================================================

_specialists_cache = {
    "data": None,
    "loaded_at": None,
    "source": None
}


def _is_cache_valid() -> bool:
    """Check if cached data is still valid."""
    if _specialists_cache["data"] is None:
        return False
    if _specialists_cache["loaded_at"] is None:
        return False
    
    age = datetime.now() - _specialists_cache["loaded_at"]
    return age < timedelta(minutes=CACHE_TTL_MINUTES)


def _update_cache(data: dict, source: str):
    """Update the cache with new data."""
    _specialists_cache["data"] = data
    _specialists_cache["loaded_at"] = datetime.now()
    _specialists_cache["source"] = source


def clear_cache():
    """Force clear the specialist cache."""
    _specialists_cache["data"] = None
    _specialists_cache["loaded_at"] = None
    _specialists_cache["source"] = None


# ============================================================
# CSV LOADER
# ============================================================

def load_from_csv(file_path: str = None) -> dict:
    """
    Load specialists from a CSV file.
    
    Expected CSV format:
    department,name,email,expertise,available
    IT_Support,Alex Chen,alex.chen@company.com,"hardware,network,security",true
    HR,Sarah Johnson,sarah.johnson@company.com,"benefits,payroll,leave",true
    
    Args:
        file_path: Path to CSV file (defaults to SPECIALISTS_CSV_PATH)
    
    Returns:
        dict: Specialists organized by department
    """
    file_path = file_path or SPECIALISTS_CSV_PATH
    specialists = {}
    
    try:
        # Try relative path first, then absolute
        if not os.path.isabs(file_path):
            # Check relative to project root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            full_path = os.path.join(project_root, file_path)
            if not os.path.exists(full_path):
                full_path = file_path
        else:
            full_path = file_path
        
        with open(full_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                department = row.get('department', '').strip()
                if not department:
                    continue
                
                if department not in specialists:
                    specialists[department] = []
                
                # Parse expertise (comma-separated)
                expertise_str = row.get('expertise', '')
                expertise = [e.strip() for e in expertise_str.split(',') if e.strip()]
                
                # Parse available (boolean)
                available_str = row.get('available', 'true').lower().strip()
                available = available_str in ('true', '1', 'yes', 'on')
                
                specialist = {
                    "name": row.get('name', '').strip(),
                    "email": row.get('email', '').strip(),
                    "expertise": expertise,
                    "available": available,
                    # Optional fields
                    "phone": row.get('phone', '').strip() or None,
                    "teams_id": row.get('teams_id', '').strip() or None,
                    "servicenow_user": row.get('servicenow_user', '').strip() or None,
                }
                
                specialists[department].append(specialist)
        
        logger.info(f"Loaded {sum(len(v) for v in specialists.values())} specialists from CSV: {full_path}")
        return specialists
    
    except FileNotFoundError:
        logger.warning(f"CSV file not found: {file_path}")
        return {}
    except Exception as e:
        logger.error(f"Error loading CSV: {e}")
        return {}


# ============================================================
# JSON LOADER
# ============================================================

def load_from_json(file_path: str = None) -> dict:
    """
    Load specialists from a JSON file.
    
    Expected JSON format:
    {
        "IT_Support": [
            {"name": "Alex Chen", "email": "alex@company.com", "expertise": ["hardware"], "available": true}
        ],
        "HR": [...]
    }
    
    Args:
        file_path: Path to JSON file (defaults to SPECIALISTS_JSON_PATH)
    
    Returns:
        dict: Specialists organized by department
    """
    file_path = file_path or SPECIALISTS_JSON_PATH
    
    try:
        # Try relative path first, then absolute
        if not os.path.isabs(file_path):
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            full_path = os.path.join(project_root, file_path)
            if not os.path.exists(full_path):
                full_path = file_path
        else:
            full_path = file_path
        
        with open(full_path, 'r', encoding='utf-8') as f:
            specialists = json.load(f)
        
        # Validate structure
        if not isinstance(specialists, dict):
            logger.error("JSON file must contain a dictionary with departments as keys")
            return {}
        
        logger.info(f"Loaded {sum(len(v) for v in specialists.values())} specialists from JSON: {full_path}")
        return specialists
    
    except FileNotFoundError:
        logger.warning(f"JSON file not found: {file_path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        return {}
    except Exception as e:
        logger.error(f"Error loading JSON: {e}")
        return {}


# ============================================================
# DATABASE LOADER
# ============================================================

def load_from_database(connection_string: str = None) -> dict:
    """
    Load specialists from a database.
    
    Supports SQLite and PostgreSQL.
    
    Expected table schema:
    CREATE TABLE specialists (
        id INTEGER PRIMARY KEY,
        department VARCHAR(50) NOT NULL,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(100) NOT NULL,
        expertise TEXT,  -- comma-separated or JSON array
        available BOOLEAN DEFAULT TRUE,
        phone VARCHAR(20),
        teams_id VARCHAR(100),
        servicenow_user VARCHAR(100)
    );
    
    Args:
        connection_string: Database connection string
    
    Returns:
        dict: Specialists organized by department
    """
    connection_string = connection_string or DB_CONNECTION_STRING
    specialists = {}
    
    try:
        if DB_TYPE == "sqlite":
            import sqlite3
            
            # Handle relative path for SQLite
            if not os.path.isabs(connection_string):
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                db_path = os.path.join(project_root, connection_string)
            else:
                db_path = connection_string
            
            if not os.path.exists(db_path):
                logger.warning(f"SQLite database not found: {db_path}")
                return {}
            
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT department, name, email, expertise, available, phone, teams_id, servicenow_user
                FROM specialists
                WHERE active = 1 OR active IS NULL
                ORDER BY department, name
            """)
            
            for row in cursor.fetchall():
                department = row['department']
                if department not in specialists:
                    specialists[department] = []
                
                # Parse expertise
                expertise_str = row['expertise'] or ''
                if expertise_str.startswith('['):
                    expertise = json.loads(expertise_str)
                else:
                    expertise = [e.strip() for e in expertise_str.split(',') if e.strip()]
                
                specialists[department].append({
                    "name": row['name'],
                    "email": row['email'],
                    "expertise": expertise,
                    "available": bool(row['available']),
                    "phone": row['phone'],
                    "teams_id": row['teams_id'],
                    "servicenow_user": row['servicenow_user'],
                })
            
            conn.close()
        
        elif DB_TYPE == "postgresql":
            try:
                import psycopg2
                import psycopg2.extras
            except ImportError:
                logger.error("psycopg2 not installed. Run: pip install psycopg2-binary")
                return {}
            
            conn = psycopg2.connect(connection_string)
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            cursor.execute("""
                SELECT department, name, email, expertise, available, phone, teams_id, servicenow_user
                FROM specialists
                WHERE active = true OR active IS NULL
                ORDER BY department, name
            """)
            
            for row in cursor.fetchall():
                department = row['department']
                if department not in specialists:
                    specialists[department] = []
                
                expertise = row['expertise']
                if isinstance(expertise, str):
                    if expertise.startswith('['):
                        expertise = json.loads(expertise)
                    else:
                        expertise = [e.strip() for e in expertise.split(',') if e.strip()]
                
                specialists[department].append({
                    "name": row['name'],
                    "email": row['email'],
                    "expertise": expertise or [],
                    "available": bool(row['available']),
                    "phone": row['phone'],
                    "teams_id": row['teams_id'],
                    "servicenow_user": row['servicenow_user'],
                })
            
            conn.close()
        
        else:
            logger.error(f"Unsupported database type: {DB_TYPE}")
            return {}
        
        logger.info(f"Loaded {sum(len(v) for v in specialists.values())} specialists from {DB_TYPE} database")
        return specialists
    
    except Exception as e:
        logger.error(f"Error loading from database: {e}")
        return {}


# ============================================================
# SERVICENOW LOADER
# ============================================================

def load_from_servicenow() -> dict:
    """
    Load specialists from ServiceNow sys_user and sys_user_group tables.
    
    Queries users who are members of assignment groups matching department names.
    
    Required environment variables:
    - SERVICENOW_INSTANCE: https://yourcompany.service-now.com
    - SERVICENOW_USERNAME or SERVICENOW_API_KEY
    - SERVICENOW_PASSWORD (if using username)
    
    Returns:
        dict: Specialists organized by department
    """
    try:
        import requests
    except ImportError:
        logger.error("requests library not installed")
        return {}
    
    instance_url = os.getenv("SERVICENOW_INSTANCE", "").rstrip('/')
    username = os.getenv("SERVICENOW_USERNAME", "")
    password = os.getenv("SERVICENOW_PASSWORD", "")
    api_key = os.getenv("SERVICENOW_API_KEY", "")
    
    if not instance_url:
        logger.warning("SERVICENOW_INSTANCE not configured")
        return {}
    
    # Mapping of ServiceNow assignment groups to our department names
    SNOW_GROUP_MAPPING = {
        os.getenv("SNOW_GROUP_IT", "IT Support"): "IT_Support",
        os.getenv("SNOW_GROUP_HR", "Human Resources"): "HR",
        os.getenv("SNOW_GROUP_SALES", "Sales Team"): "Sales",
        os.getenv("SNOW_GROUP_LEGAL", "Legal Department"): "Legal",
    }
    
    specialists = {}
    
    try:
        # Set up authentication
        if api_key:
            headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
            auth = None
        else:
            headers = {"Accept": "application/json"}
            auth = (username, password)
        
        for snow_group, department in SNOW_GROUP_MAPPING.items():
            # First, get the group sys_id
            group_url = f"{instance_url}/api/now/table/sys_user_group"
            group_params = {
                "sysparm_query": f"name={snow_group}",
                "sysparm_limit": 1,
                "sysparm_fields": "sys_id,name"
            }
            
            response = requests.get(group_url, params=group_params, headers=headers, auth=auth, timeout=30)
            if response.status_code != 200:
                logger.warning(f"Could not find ServiceNow group: {snow_group}")
                continue
            
            groups = response.json().get("result", [])
            if not groups:
                continue
            
            group_sys_id = groups[0]["sys_id"]
            
            # Get group members
            member_url = f"{instance_url}/api/now/table/sys_user_grmember"
            member_params = {
                "sysparm_query": f"group={group_sys_id}",
                "sysparm_fields": "user.name,user.email,user.phone,user.sys_id,user.active"
            }
            
            response = requests.get(member_url, params=member_params, headers=headers, auth=auth, timeout=30)
            if response.status_code != 200:
                continue
            
            members = response.json().get("result", [])
            
            if department not in specialists:
                specialists[department] = []
            
            for member in members:
                user = member.get("user", {})
                if not user.get("active", True):
                    continue
                
                specialists[department].append({
                    "name": user.get("name", "Unknown"),
                    "email": user.get("email", ""),
                    "expertise": [],  # ServiceNow doesn't have this by default
                    "available": True,  # Could check schedule/availability
                    "phone": user.get("phone", ""),
                    "servicenow_user": user.get("sys_id", ""),
                })
        
        logger.info(f"Loaded {sum(len(v) for v in specialists.values())} specialists from ServiceNow")
        return specialists
    
    except Exception as e:
        logger.error(f"Error loading from ServiceNow: {e}")
        return {}


# ============================================================
# LDAP/ACTIVE DIRECTORY LOADER
# ============================================================

def load_from_ldap() -> dict:
    """
    Load specialists from Active Directory/LDAP.
    
    Queries users who are members of AD groups matching department names.
    
    Required environment variables:
    - LDAP_SERVER: ldap://ldap.company.com:389
    - LDAP_USE_SSL: true/false
    - LDAP_BASE_DN: dc=company,dc=com
    - LDAP_BIND_DN: cn=service,dc=company,dc=com
    - LDAP_BIND_PASSWORD: password
    
    Returns:
        dict: Specialists organized by department
    """
    try:
        import ldap3  # type: ignore[import-not-found]
        from ldap3 import Server, Connection, ALL, SUBTREE  # type: ignore[import-not-found]
    except ImportError:
        logger.error("ldap3 library not installed. Run: pip install ldap3")
        return {}
    
    ldap_server = os.getenv("LDAP_SERVER", "")
    use_ssl = os.getenv("LDAP_USE_SSL", "false").lower() == "true"
    base_dn = os.getenv("LDAP_BASE_DN", "")
    bind_dn = os.getenv("LDAP_BIND_DN", "")
    bind_password = os.getenv("LDAP_BIND_PASSWORD", "")
    
    if not ldap_server or not base_dn:
        logger.warning("LDAP not configured (LDAP_SERVER and LDAP_BASE_DN required)")
        return {}
    
    # Mapping of AD groups to our department names
    AD_GROUP_MAPPING = {
        os.getenv("AD_GROUP_IT", "CN=IT Support,OU=Groups"): "IT_Support",
        os.getenv("AD_GROUP_HR", "CN=Human Resources,OU=Groups"): "HR",
        os.getenv("AD_GROUP_SALES", "CN=Sales Team,OU=Groups"): "Sales",
        os.getenv("AD_GROUP_LEGAL", "CN=Legal Department,OU=Groups"): "Legal",
    }
    
    specialists = {}
    
    try:
        # Connect to LDAP server
        server = Server(ldap_server, use_ssl=use_ssl, get_info=ALL)
        conn = Connection(server, user=bind_dn, password=bind_password, auto_bind=True)
        
        for ad_group, department in AD_GROUP_MAPPING.items():
            # Search for group members
            # The group DN should include the base_dn
            group_dn = f"{ad_group},{base_dn}" if base_dn not in ad_group else ad_group
            
            # Get members of the group
            search_filter = f"(&(objectClass=user)(memberOf={group_dn}))"
            
            conn.search(
                search_base=base_dn,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=['cn', 'mail', 'telephoneNumber', 'userAccountControl', 'sAMAccountName']
            )
            
            if department not in specialists:
                specialists[department] = []
            
            for entry in conn.entries:
                # Check if account is enabled (userAccountControl bit 2 = disabled)
                uac = entry.userAccountControl.value if hasattr(entry, 'userAccountControl') else 0
                is_active = not (uac & 2) if uac else True
                
                if not is_active:
                    continue
                
                specialists[department].append({
                    "name": str(entry.cn) if hasattr(entry, 'cn') else "Unknown",
                    "email": str(entry.mail) if hasattr(entry, 'mail') else "",
                    "expertise": [],  # AD doesn't have this by default
                    "available": True,
                    "phone": str(entry.telephoneNumber) if hasattr(entry, 'telephoneNumber') else "",
                    "teams_id": str(entry.mail) if hasattr(entry, 'mail') else "",  # Teams uses email
                })
        
        conn.unbind()
        logger.info(f"Loaded {sum(len(v) for v in specialists.values())} specialists from LDAP")
        return specialists
    
    except Exception as e:
        logger.error(f"Error loading from LDAP: {e}")
        return {}


# ============================================================
# STATIC/FALLBACK DATA
# ============================================================

STATIC_SPECIALISTS = {
    "IT_Support": [
        {"name": "Alex Chen", "email": "alex.chen@company.com", "expertise": ["hardware", "network", "security"], "available": True},
        {"name": "Maria Garcia", "email": "maria.garcia@company.com", "expertise": ["software", "licenses", "cloud"], "available": True},
        {"name": "James Wilson", "email": "james.wilson@company.com", "expertise": ["infrastructure", "servers", "databases"], "available": False},
    ],
    "HR": [
        {"name": "Sarah Johnson", "email": "sarah.johnson@company.com", "expertise": ["benefits", "payroll", "leave"], "available": True},
        {"name": "Michael Brown", "email": "michael.brown@company.com", "expertise": ["recruiting", "onboarding", "policies"], "available": True},
        {"name": "Emily Davis", "email": "emily.davis@company.com", "expertise": ["employee_relations", "performance", "training"], "available": False},
    ],
    "Sales": [
        {"name": "David Lee", "email": "david.lee@company.com", "expertise": ["enterprise", "contracts", "pricing"], "available": True},
        {"name": "Jennifer Martinez", "email": "jennifer.martinez@company.com", "expertise": ["smb", "demos", "proposals"], "available": True},
    ],
    "Legal": [
        {"name": "Robert Taylor", "email": "robert.taylor@company.com", "expertise": ["contracts", "compliance", "ip"], "available": True},
        {"name": "Lisa Anderson", "email": "lisa.anderson@company.com", "expertise": ["employment_law", "policies", "disputes"], "available": False},
    ]
}


# ============================================================
# MAIN LOADER FUNCTION
# ============================================================

def load_specialists(force_reload: bool = False) -> dict:
    """
    Load specialists from the configured source.
    
    Uses caching to avoid repeated API/DB calls.
    
    Args:
        force_reload: If True, bypass cache and reload from source
    
    Returns:
        dict: Specialists organized by department
    """
    global _specialists_cache
    
    # Check cache first (unless force reload)
    if not force_reload and _is_cache_valid():
        logger.debug(f"Using cached specialists (source: {_specialists_cache['source']})")
        return _specialists_cache["data"]
    
    source = SPECIALIST_SOURCE.lower()
    specialists = {}
    
    if source == "csv":
        specialists = load_from_csv()
    elif source == "json":
        specialists = load_from_json()
    elif source == "database" or source == "db":
        specialists = load_from_database()
    elif source == "servicenow" or source == "snow":
        specialists = load_from_servicenow()
    elif source == "ldap" or source == "ad" or source == "activedirectory":
        specialists = load_from_ldap()
    elif source == "static":
        specialists = STATIC_SPECIALISTS.copy()
    else:
        logger.warning(f"Unknown SPECIALIST_SOURCE: {source}, falling back to static")
        specialists = STATIC_SPECIALISTS.copy()
    
    # Fallback to static if no data loaded
    if not specialists:
        logger.warning(f"No specialists loaded from {source}, falling back to static data")
        specialists = STATIC_SPECIALISTS.copy()
    
    # Update cache
    _update_cache(specialists, source)
    
    return specialists


def get_specialist_by_email(email: str) -> Optional[dict]:
    """
    Find a specialist by email address.
    
    Args:
        email: Email address to search for
    
    Returns:
        dict: Specialist info or None if not found
    """
    specialists = load_specialists()
    email_lower = email.lower()
    
    for department, dept_specialists in specialists.items():
        for specialist in dept_specialists:
            if specialist.get("email", "").lower() == email_lower:
                return {**specialist, "department": department}
    
    return None


def get_available_specialists(department: str = None) -> list:
    """
    Get all available specialists, optionally filtered by department.
    
    Args:
        department: Optional department filter
    
    Returns:
        list: Available specialists
    """
    specialists = load_specialists()
    available = []
    
    departments = [department] if department else specialists.keys()
    
    for dept in departments:
        if dept not in specialists:
            continue
        for specialist in specialists[dept]:
            if specialist.get("available", True):
                available.append({**specialist, "department": dept})
    
    return available


# ============================================================
# CLI FOR TESTING
# ============================================================

if __name__ == "__main__":
    import sys
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Test loading from different sources
    if len(sys.argv) > 1:
        source = sys.argv[1]
        print(f"\nTesting {source} loader...")
        
        if source == "csv":
            data = load_from_csv()
        elif source == "json":
            data = load_from_json()
        elif source == "database":
            data = load_from_database()
        elif source == "servicenow":
            data = load_from_servicenow()
        elif source == "ldap":
            data = load_from_ldap()
        else:
            data = STATIC_SPECIALISTS
    else:
        print(f"\nLoading specialists from configured source: {SPECIALIST_SOURCE}")
        data = load_specialists()
    
    print(f"\nLoaded specialists:")
    for dept, specialists in data.items():
        print(f"\n{dept}:")
        for s in specialists:
            status = "✓" if s.get("available") else "✗"
            print(f"  {status} {s['name']} <{s['email']}>")
    
    print(f"\nTotal: {sum(len(v) for v in data.values())} specialists across {len(data)} departments")
