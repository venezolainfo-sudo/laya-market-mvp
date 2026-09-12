import type { ComponentType } from 'react';

declare const LocationMap: ComponentType<{
  latitude: number;
  longitude: number;
  onChange?: (latitude: number, longitude: number) => void;
  markers?: Array<{id:string;latitude:number;longitude:number;name?:string;distance_km?:number}>;
}>;

export default LocationMap;
