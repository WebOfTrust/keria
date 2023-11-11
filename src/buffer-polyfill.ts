import { Buffer } from 'buffer';

try {
    window.Buffer = Buffer;
} catch (e) {}
