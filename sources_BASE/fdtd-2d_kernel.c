
void kernel_fdtd_2d(double ex[60][80], double ey[60][80], double hz[60][80],
                    double _fict_[40]) {
    int t;
    int i;
    int j;

    L0: for (t = 0; t < 40; t++) {
    // @slot __PIPE__L0
    // @slot __UNROLL__L0

        L1: for (j = 0; j < 80; j++) {
        // @slot __PIPE__L1
        // @slot __UNROLL__L1

            ey[0][j] = _fict_[t];
        }

        L2: for (i = 1; i < 60; i++) {
        // @slot __PIPE__L2
        // @slot __UNROLL__L2

            L5: for (j = 0; j < 80; j++) {
            // @slot __PIPE__L5
            // @slot __UNROLL__L5

                ey[i][j] = ey[i][j] - 0.5 * (hz[i][j] - hz[i - 1][j]);
            }
        }

        L3: for (i = 0; i < 60; i++) {
        // @slot __PIPE__L3
        // @slot __UNROLL__L3

            L6: for (j = 1; j < 80; j++) {
            // @slot __PIPE__L6
            // @slot __UNROLL__L6

                ex[i][j] = ex[i][j] - 0.5 * (hz[i][j] - hz[i][j - 1]);
            }
        }

        L4: for (i = 0; i < 59; i++) {
        // @slot __PIPE__L4
        // @slot __UNROLL__L4

            L7: for (j = 0; j < 79; j++) {
            // @slot __PIPE__L7
            // @slot __UNROLL__L7

                hz[i][j] = hz[i][j] - 0.7 * (ex[i][j + 1] - ex[i][j] + ey[i + 1][j] - ey[i][j]);
            }
        }
    }
}
