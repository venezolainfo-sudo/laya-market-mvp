import type { ComponentType } from 'react';

declare const LocationMap: ComponentType<{
  latitude: number;
  longitude: number;
  onChange?: (latitude: number, longitude: number) => void;
}>;

export default LocationMap;
