import React from 'react';
import {View,StyleSheet} from 'react-native';
import {registerRootComponent} from 'expo';
import App from './App';
import UserOpsWidget from './UserOpsWidget';
function Root(){return <View style={styles.root}><App/><UserOpsWidget/></View>}
const styles=StyleSheet.create({root:{flex:1}});
registerRootComponent(Root);
