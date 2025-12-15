// Jest 전역 설정
import '@testing-library/jest-dom'
import { TextEncoder, TextDecoder } from 'util'

// TextEncoder/TextDecoder polyfill for jsdom environment
global.TextEncoder = TextEncoder
global.TextDecoder = TextDecoder

// Web Crypto API polyfill for jsdom environment
if (typeof global.crypto === 'undefined') {
  const { webcrypto } = require('crypto');
  global.crypto = webcrypto;
}

