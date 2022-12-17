
export {}


export class IndexerCodex {
    Ed25519_Sig: string = 'A'  // Ed25519 sig appears same in both lists if any.
    Ed25519_Crt_Sig: string = 'B'  // Ed25519 sig appears in current list only.
    ECDSA_256k1_Sig: string = 'C'  // ECDSA secp256k1 sig appears same in both lists if any.
    ECDSA_256k1_Crt_Sig: string = 'D'  // ECDSA secp256k1 sig appears in current list.
    Ed448_Sig: string = '0A'  // Ed448 signature appears in both lists.
    Ed448_Crt_Sig: string = '0B'  // Ed448 signature appears in current list only.
    Ed25519_Big_Sig: string = '2A'  // Ed25519 sig appears in both lists.
    Ed25519_Big_Crt_Sig: string = '2B'  // Ed25519 sig appears in current list only.
    ECDSA_256k1_Big_Sig: string = '2C'  // ECDSA secp256k1 sig appears in both lists.
    ECDSA_256k1_Big_Crt_Sig: string = '2D'  // ECDSA secp256k1 sig appears in current list only.
    Ed448_Big_Sig: string = '3A'  // Ed448 signature appears in both lists.
    Ed448_Big_Crt_Sig: string = '3B'  // Ed448 signature appears in current list only.
    
}

export const IdrDex = new IndexerCodex()




