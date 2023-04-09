# screw-sorter-sw

Example command to run to generate sim images
`blender side_profile_2.blend --background --python ./scripts/run_sim.py`

To install proper packages
`conda install --file requirements.txt`

Working models:
    - M2 vs M3
        - Works in sim, test set in reality, need to check real time cam 
        - `model_v1_m2vsm3.pt`
    - demo
        - Implemting
        - Should predict thread diameter, imperial and metric between:
            - M3, M3.5, M4,
            - I4, I6, I8,
        - CAD models to train from
            - M3x0.5mm, I4x48(0.529mm) with lengths:
                - 6mm, 1/4" (6.35mm)
                    - 92095A179, 92949A327
                - 10mm, 3/8" (9.53mm)
                    - 92095A182, 92949A328
                - 12mm, 1/2"(12.70mm)
                    - 92095A183, 92949A329
            - M3.5x0.6mm, I6x40(0.635mm) with lengths:
                - 6mm, 1/4" (6.35mm)
                    - 92095A159, 92949A337
                - 10mm, 3/8" (9.53mm)
                    - 92095A161, 92949A338
                - 14mm, 1/2" (12.70mm)
                    - 92095A124, 92949A419
            - M4x0.7mm, I8x36(0.706mm) with lengths:
                - 6mm, 1/4" (6.35mm)
                    - 92095A188, 92949A424
                - 12mm, 1/2"(12.70mm)
                    - 92095A192, 92949A426
                - 20mm, 3/4"(19.05mm)
                    - 92095A196, 91255A837
