import React from 'react';
import MapView,{Marker} from 'react-native-maps';

export default function LocationMap({latitude,longitude,onChange,markers=[]}:{latitude:number;longitude:number;onChange?:(lat:number,lng:number)=>void;markers?:any[]}){
  return <MapView style={{width:'100%',height:260,borderRadius:18}} region={{latitude,longitude,latitudeDelta:0.025,longitudeDelta:0.025}} onPress={e=>onChange?.(e.nativeEvent.coordinate.latitude,e.nativeEvent.coordinate.longitude)}>
    <Marker coordinate={{latitude,longitude}} draggable onDragEnd={e=>onChange?.(e.nativeEvent.coordinate.latitude,e.nativeEvent.coordinate.longitude)} title="Tu ubicación"/>
    {markers.filter(x=>x.latitude&&x.longitude).map(x=><Marker key={x.id} coordinate={{latitude:x.latitude,longitude:x.longitude}} title={x.name} description={x.distance_km?`${x.distance_km} km`:undefined}/>) }
  </MapView>
}
