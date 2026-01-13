
void bbgemm(double m1[4096], double m2[4096], double prod[4096]) {
    int i;
    int k;
    int j;
    int jj;
    int kk;
    int i_row;
    int k_row;
    double temp_x;
    double mul;

    /* Standardize from: for(jj = 0;jj < 64;jj += 8) {...} */
    L0: for (jj = 0; jj <= 7; jj++) {
        // @slot __PIPE__L0

        int _in_jj = 0 + 8L * jj;

        /* Standardize from: for(kk = 0;kk < 64;kk += 8) {...} */
        L1: for (kk = 0; kk <= 7; kk++) {
                // @slot __PIPE__L1

                int _in_kk = 0 + 8L * kk;

                L2: for (i = 0; i < 64; ++i) {
                    // @slot __PIPE__L2
                    // @slot __UNROLL__L2

                    L3: for (k = 0; k < 8; ++k) {
                        // @slot __PIPE__L3

                        i_row = i * 64;
                        k_row = (k + _in_kk) * 64;
                        temp_x = m1[i_row + k + _in_kk];

                        L4: for (j = 0; j < 8; ++j) {
                            // @slot __UNROLL__L4

                            mul = temp_x * m2[k_row + j + _in_jj];
                            prod[i_row + j + _in_jj] += mul;
                        }
                    }
                }
            }
            kk = 56 + 8L;
    }
    jj = 56 + 8L;
}
