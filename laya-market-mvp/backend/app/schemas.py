from pydantic import BaseModel, EmailStr, Field
from typing import Literal
class LoginIn(BaseModel): email: EmailStr; password: str
class TokenOut(BaseModel): access_token: str; token_type: str='bearer'; role: str; name: str
class ProductIn(BaseModel): name:str; category_id:str; description:str|None=None; image_url:str|None=None; price:float=Field(gt=0); currency:Literal['ARS','USD']='ARS'; stock:int=Field(ge=0); unit:str='unidad'; active:bool=True
class OrderItemIn(BaseModel): product_id:str; quantity:int=Field(gt=0)
class OrderIn(BaseModel): business_id:str; items:list[OrderItemIn]; currency:Literal['ARS','USD']; delivery_method:Literal['OWN_DELIVERY','COURIER']; delivery_address:str; payment_method:Literal['CASH','TRANSFER','MERCADO_PAGO','SIMULATED']='SIMULATED'; delivery_fee:float=Field(ge=0, default=0)
class BusinessIn(BaseModel): name:str; description:str|None=None; country:Literal['AR','VE']; city:str; address:str; own_delivery:bool=True; courier_enabled:bool=True
class PaymentIntentIn(BaseModel): order_id:str; provider:Literal['SIMULATED','MERCADO_PAGO']='SIMULATED'
