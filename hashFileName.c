#import <string.h>
#include <stdio.h>
#include <stdint.h>

static inline uint16_t rotl16(uint16_t value, uint8_t shift) {
    // Masking the shift with 15 prevents undefined behavior 
    // if shift is >= 16
    return (value << (shift & 15)) | (value >> ((16 - shift) & 15));
}

int hashFileNameMM4( char *name, int len )
{
  int i, h;

  if( len < 1 ) return( -1 );

  for( i = 1, h = name[0] ; i < len ; h += name[i++] )
  {
    // Rotate the bits in 'h' right 7 places
    // In assembly it would be: ror h, 7
    // 01234567 89ABCDEF -> 9ABCDEF0 12345678
    // 0x007F = 00000000 01111111
    // 0xFF80 = 11111111 10000000
    h = ( h & 0x007F ) << 9 | ( h & 0xFF80 ) >> 7;
  }

  return( h );
}

uint16_t hashFileNameMM3(const char* fileName, int len)
{
  uint16_t hash = 0;
  while (0 != *fileName)
  {
    uint8_t c = ((*fileName & 0x7F) < 0x60) ? *fileName : *fileName - 0x20;
    hash = rotl16(hash, 9);  // xchg bl, bh | rol bx, 1
    hash += c;
    fileName++;
  }
  return hash;
}

int main(int argc,char* argv[]){

  if (strlen(argv[1]) >= 0){
    int mm4hash = hashFileNameMM4(argv[1], strlen(argv[1]));
    printf("MM4 Hash: %d\n", mm4hash);
    printf("MM4 Dec : %04x\n", mm4hash);
    int mm3hash = hashFileNameMM3(argv[1], strlen(argv[1]));
    printf("MM3 Hash: %d\n", mm3hash);
    printf("MM3 Dec : %04x\n", mm3hash);
  }

}
