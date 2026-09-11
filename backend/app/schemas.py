from pydantic import BaseModel, EmailStr, Field
from typing import Literal
UnitType=Literal['unidad','g','kg','ml','l','paquete','caja','docena','porcion','combo']
class LoginIn(BaseModel): email: EmailStr; password: str
class TokenOut(BaseModel): access_token: str; token_type: str='bearer'; role: str; name: str
class PresentationIn(BaseModel): label:str; amount:float=Field(gt=0); unit:UnitType='unidad'; price:float=Field(gt=0); stock:int=Field(ge=0); active:bool=True
class ProductIn(BaseModel):
    name:str; category_id:str; description:str|None=None; image_url:str|None=None; price:float=Field(gt=0); currency:Literal['ARS','USD']='ARS'; stock:int=Field(ge=0); unit:UnitType='unidad'; amount:float=Field(gt=0,default=1); brand:str|None=None; sku:str|None=None; featured:bool=False; active:bool=True; presentations:list[PresentationIn]=[]
class OrderItemIn(BaseModel): product_id:str; quantity:int=Field(gt=0)
class OrderIn(BaseModel): business_id:str; items:list[OrderItemIn]; currency:Literal['ARS','USD']; delivery_method:Literal['OWN_DELIVERY','COURIER']; delivery_address:str; payment_method:Literal['CASH','TRANSFER','MERCADO_PAGO','SIMULATED']='SIMULATED'; delivery_fee:float=Field(ge=0, default=0)
class BusinessIn(BaseModel): name:str; description:str|None=None; business_type_id:str|None=None; country:Literal['AR','VE']; city:str; address:str; own_delivery:bool=True; courier_enabled:bool=True
class BusinessTypeIn(BaseModel): name:str; slug:str; icon:str='🏪'; active:bool=True; order_index:int=0
class CategoryIn(BaseModel): name:str; slug:str; icon:str='🛒'; parent_id:str|None=None; business_type_id:str|None=None; active:bool=True; order_index:int=0
class PaymentIntentIn(BaseModel): order_id:str; provider:Literal['SIMULATED','MERCADO_PAGO']='SIMULATED'
