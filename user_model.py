from sqlalchemy import Column,Integer,String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from passlib.apps import custom_app_context as pwd_context
import random, string
from itsdangerous import(TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)

Base = declarative_base()
secret_key = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    picture = Column(String)
    email = Column(String)
    password_hash = Column(String(64))

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def generate_auth_token(self, expiration=600):
        s = Serializer(secret_key, expires_in = expiration)
        return s.dumps({'id': self.id })

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(secret_key)
        try:
            data = s.loads(token)
        except SignatureExpired:
            #Valid Token, but expired
            return None
        except BadSignature:
            #Invalid Token
            return None
        user_id = data['id']
        return user_id

    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
            'email': self.email,
           'picture': self.picture,
       }
 

class Request(Base):
    __tablename__ = 'Request'


    user_id =Column(Integer)
    meal_type =Column(String(80), nullable = False)
    location_string = Column(String(20))
    latitude = Column(Integer)
    
    longitude = Column(Integer)
    meal_time = Column(String(20))
    id = Column(Integer, primary_key = True)
    filled = Column(String(250))

    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'meal_type': self.meal_type,
           'location_string' : self.location_string,
           'latitude': self.latitude,
           'longitude': self.longitude,
           'meal_time' : self.meal_time
           #'filled': self.filled
       }


class Proposal(Base):
    __tablename__ = 'Proposal'


    user_proposed_to =Column(String(80), nullable = False)
    user_proposed_from =Column(String(80), nullable = False)
    request_id = Column(Integer)
    id = Column(Integer, primary_key=True)
    filled = Column(String(250))

    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
            'user_proposed_to': self.user_proposed_to,
           'user_proposed_from': self.user_proposed_from,
           'request_id' : self.request_id
           'id': self.id
           #'filled': self.filled
       }

class MealDate(Base):
    __tablename__ = 'Mealdate'


    user1 =Column(String(80), nullable = False)
    user2 =Column(String(80), nullable = False)
    restaurant_name = Column(String(200))
    restaurant_address = Column(String(200))
    restaurant_picture = Column(String(200))
    meal_time = Column(String(20))
    id = Column(Integer, primary_key=True)
    filled = Column(String(250))

    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
            'user1': self.user1,
           'user2': self.user2,
           'restaurant_name' : self.restaurant_name           
           'restaurant_address': self.restaurant_address
           'restaurant_picture': self.restaurant_picture
           'meal_time': self.meal_time
           #'filled': self.filled
       }

engine = create_engine('sqlite:///User.db')
 

Base.metadata.create_all(engine)