import React from 'react';
import {View,Text} from 'react-native';

export default function LocationMap({latitude,longitude}:{latitude:number;longitude:number}){
  const src=`https://www.openstreetmap.org/export/embed.html?bbox=${longitude-0.02}%2C${latitude-0.02}%2C${longitude+0.02}%2C${latitude+0.02}&layer=mapnik&marker=${latitude}%2C${longitude}`;
  return <View style={{width:'100%',height:260,borderRadius:18,overflow:'hidden',backgroundColor:'#0B1933'}}>
    {React.createElement('iframe' as any,{src,style:{border:0,width:'100%',height:'100%'},title:'Mapa LAYA Market'})}
    <Text style={{position:'absolute',left:10,bottom:8,backgroundColor:'#020611DD',color:'#fff',padding:6,borderRadius:8}}>Ubicación seleccionada</Text>
  </View>
}
