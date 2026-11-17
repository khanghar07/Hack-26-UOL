// React/Vite frontend handoff: install firebase, then import auth from this module.
import { initializeApp } from 'firebase/app';
import { getAuth, connectAuthEmulator } from 'firebase/auth';
const local = import.meta.env.VITE_AUTH_EMULATOR === 'true';
const app = initializeApp(local ? {apiKey:'demo',projectId:'demo-novaworks',appId:'demo'} : {
  apiKey: 'AIzaSyD1cOQjQlEzdmZJrTjE0FRCUMljhHCQZwk',
  authDomain: 'hack-26-uol.firebaseapp.com',
  projectId: 'hack-26-uol',
  storageBucket: 'hack-26-uol.firebasestorage.app',
  messagingSenderId: '415622058150',
  appId: '1:415622058150:web:d680f9fafa327a6c0b2467',
});
export const auth = getAuth(app);
if(local) connectAuthEmulator(auth,'http://127.0.0.1:9099',{disableWarnings:true});
