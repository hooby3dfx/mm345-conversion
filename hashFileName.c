#import <string.h>
#include <stdio.h>


int hashFileName( char *name, int len )
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

int main(int argc,char* argv[]){

  if (strlen(argv[1]) >= 0){
    int hash = hashFileName(argv[1], strlen(argv[1]));
    printf("%d\n", hash);
    printf("%04x\n", hash);
  }

}
