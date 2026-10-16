import { EventEmitter } from 'events';

export const events = new EventEmitter(); // 'change' -> { entity, op }
