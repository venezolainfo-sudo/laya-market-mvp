import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Location from 'expo-location';
import * as TaskManager from 'expo-task-manager';

export const COURIER_LOCATION_TASK='laya-courier-background-location';
const API=process.env.EXPO_PUBLIC_API_URL||'http://localhost:8000/api/v1';
const ACTIVE_DELIVERY_KEY='laya_courier_active_delivery';

TaskManager.defineTask(COURIER_LOCATION_TASK,async({data,error})=>{
  if(error||!data)return;
  const payload=data as {locations?:Location.LocationObject[]};
  const locations=payload.locations||[];
  const latest=locations[locations.length-1];
  if(!latest)return;
  const deliveryId=await AsyncStorage.getItem(ACTIVE_DELIVERY_KEY);
  if(!deliveryId)return;
  const token=await AsyncStorage.getItem('token');
  try{
    await fetch(`${API}/courier/location`,{
      method:'POST',
      headers:{'Content-Type':'application/json',...(token?{Authorization:`Bearer ${token}`}:{})},
      body:JSON.stringify({latitude:latest.coords.latitude,longitude:latest.coords.longitude,accuracy:latest.coords.accuracy,delivery_id:deliveryId})
    });
  }catch{}
});

export async function setActiveDelivery(id:string|null){
  if(id)await AsyncStorage.setItem(ACTIVE_DELIVERY_KEY,id);else await AsyncStorage.removeItem(ACTIVE_DELIVERY_KEY);
}

export async function isBackgroundTrackingActive(){
  return Location.hasStartedLocationUpdatesAsync(COURIER_LOCATION_TASK);
}

export async function startBackgroundTracking(deliveryId:string){
  const fg=await Location.requestForegroundPermissionsAsync();
  if(fg.status!=='granted')throw new Error('Permiso de ubicación rechazado');
  const bg=await Location.requestBackgroundPermissionsAsync();
  if(bg.status!=='granted')throw new Error('Se requiere ubicación en segundo plano para una entrega activa');
  await setActiveDelivery(deliveryId);
  const started=await Location.hasStartedLocationUpdatesAsync(COURIER_LOCATION_TASK);
  if(started)return;
  await Location.startLocationUpdatesAsync(COURIER_LOCATION_TASK,{
    accuracy:Location.Accuracy.High,
    distanceInterval:15,
    timeInterval:10000,
    deferredUpdatesDistance:20,
    deferredUpdatesInterval:15000,
    pausesUpdatesAutomatically:false,
    showsBackgroundLocationIndicator:true,
    foregroundService:{notificationTitle:'LAYA Market · Entrega activa',notificationBody:'Compartiendo ubicación durante la entrega.'}
  });
}

export async function stopBackgroundTracking(){
  const started=await Location.hasStartedLocationUpdatesAsync(COURIER_LOCATION_TASK);
  if(started)await Location.stopLocationUpdatesAsync(COURIER_LOCATION_TASK);
  await setActiveDelivery(null);
}
