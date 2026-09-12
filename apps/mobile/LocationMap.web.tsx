import React from 'react';
import {View,Text} from 'react-native';

export default function LocationMap({latitude,longitude,markers=[]}:{latitude:number;longitude:number;markers?:any[]}){
  const focus=markers.find((x:any)=>x.id==='courier')||markers[0];
  const lat=focus?.latitude??latitude,lng=focus?.longitude??longitude;
  const src=`https://www.openstreetmap.org/export/embed.html?bbox=${lng-0.02}%2C${lat-0.02}%2C${lng+0.02}%2C${lat+0.02}&layer=mapnik&marker=${lat}%2C${lng}`;
  return <View style={{width:'100%',height:260,borderRadius:18,overflow:'hidden',backgroundColor:'#0B1933'}}>
    {React.createElement('iframe' as any,{src,style:{border:0,width:'100%',height:'100%'},title:'Mapa LAYA Market'})}
    <Text style={{position:'absolute',left:10,bottom:8,backgroundColor:'#020611DD',color:'#fff',padding:6,borderRadius:8}}>{focus?.name||'Ubicación seleccionada'}</Text>
  </View>
}
