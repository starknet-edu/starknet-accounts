// Basic definitions for the secp256k1 elliptic curve.
// The curve is given by the equation
//   y^2 = x^3 + 7
// over the field Z/p for
//   p = secp256k1_prime = 2 ** 256 - (2 ** 32 + 2 ** 9 + 2 ** 8 + 2 ** 7 + 2 ** 6 + 2 ** 4 + 1).
// The size of the curve is
//   n = 0xfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141 (prime).

// SECP_REM is defined by the equation:
//   secp256k1_prime = 2 ** 256 - SECP_REM.
const SECP_REM = 2 ** 32 + 2 ** 9 + 2 ** 8 + 2 ** 7 + 2 ** 6 + 2 ** 4 + 1;

// The following constants represent the size of the secp256k1 curve:
//   n = N0 + BASE * N1 + BASE**2 * N2.
const N0 = 0x8a03bbfd25e8cd0364141;
const N1 = 0x3ffffffffffaeabb739abd;
const N2 = 0xfffffffffffffffffffff;
