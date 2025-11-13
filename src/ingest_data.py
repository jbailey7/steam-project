from endpoints import get_app_list
from db import SessionLocal
from models import Base

def add_data():
    app_list = get_app_list()
    
    # with SessionLocal() as s, s.begin():
    #     Base.metadata.create_all(s.get_bind())