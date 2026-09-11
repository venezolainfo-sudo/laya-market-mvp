from pydantic import BaseModel, EmailStr, Field
from typing import Literal
UnitType=Literal['unidad','g','kg','ml','l','paquete','caja','docena','porcion','combo']
DeliveryMethod=Literal['OWN_DELIVERY','COURIER','PICKUP']
class LoginIn(BaseModel): email: EmailStr; password: str
class TokenOut(BaseModel): access_token: str; token_type: str='bearer'; role: str; name: str
class PresentationIn(BaseModel): label:str; amount:float=Field(gt=0); unit:UnitType='unidad'; price:float=Field(gt=0); stock:int=Field(ge=0); active:bool=True
class ProductIn(BaseModel): name:str; category_id:str; description:str|None=None; image_url:str|None=None; price:float=Field(gt=0); currency:Literal['ARS','USD']='ARS'; stock:int=Field(ge=0); unit:UnitType='unidad'; amount:float=Field(gt=0,default=1); brand:str|None=None; sku:str|None=None; featured:bool=False; active:bool=True
class CartItemIn(BaseModel): product_id:str; quantity:int=Field(gt=0); presentation_id:str|None=None
class CheckoutQuoteIn(BaseModel): business_id:str; items:list[CartItemIn]; currency:Literal['ARS','USD']; delivery_method:DeliveryMethod; address_id:str|None=None
class OrderIn(CheckoutQuoteIn): payment_method:Literal['CASH','TRANSFER','MERCADO_PAGO','PAYPAL','SIMULATED']='SIMULATED'; notes:str|None=Field(default=None,max_length=500)
class BusinessIn(BaseModel): name:str; description:str|None=None; business_type_id:str|None=None; country:Literal['AR','VE']; city:str; address:str; own_delivery:bool=True; courier_enabled:bool=True
class BusinessDeliveryIn(BaseModel): latitude:float; longitude:float; delivery_radius_km:float=Field(gt=0,le=100); delivery_base_fee:float=Field(ge=0); delivery_per_km:float=Field(ge=0); delivery_min_fee:float=Field(ge=0); own_delivery:bool=True; courier_enabled:bool=True; pickup_enabled:bool=True
class BusinessTypeIn(BaseModel): name:str; slug:str; icon:str='🏪'; active:bool=True; order_index:int=0
class CategoryIn(BaseModel): name:str; slug:str; icon:str='🛒'; parent_id:str|None=None; business_type_id:str|None=None; active:bool=True; order_index:int=0
class AddressIn(BaseModel): label:str='Casa'; line1:str; city:str; province:str; country:Literal['AR','VE']; postal_code:str|None=None; reference:str|None=None; latitude:float|None=None; longitude:float|None=None; is_default:bool=False
class PaymentIntentIn(BaseModel): order_id:str; provider:Literal['SIMULATED','MERCADO_PAGO','PAYPAL']='SIMULATED'
