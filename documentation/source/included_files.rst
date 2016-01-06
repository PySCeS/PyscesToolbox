Included Files
==============

Here are the files that are used in the examples as well as the interactive
notebook versions of the documentation

Models
------

The models used in this documentation are included below (together with their
layout files). These files must be downloaded to the ``psc`` directory to be
used in the example notebooks unless otherwise specified.

example_model.psc
^^^^^^^^^^^^^^^^^

.. image:: included_files_files/example_model.png



:download:`model <included_files/example_model.psc>`
:download:`layout file <included_files/example_model_layout.dict>`

The text of ``example_model.psc`` is included below:

.. code:: python

    # example_model.psc
    # -----------------------------------------------------------------------------
    # Fixed Species

    FIX: X0 X2 X3

    # -----------------------------------------------------------------------------
    # Reaction definitions

    R1:
        X0 = S1
        ((Vf1 / Km1_X0) * (X0 - S1 / Keq1)) / (1 + X0/Km1_X0 + S1/Km1_S1)

    R2:
        S1 = X2
        ((Vf2 / Km2_S1) * (S1 - X2 / Keq2)) / (1 + S1/Km2_S1 + X2/Km2_X2)

    R3:
        S1 = X3
        ((Vf3 / Km3_S1) * (S1 - X3 / Keq3)) / (1 + S1/Km3_S1 + X3/Km3_X3)

    # -----------------------------------------------------------------------------
    # Variable species initital concentrations

    S1 = 1

    # -----------------------------------------------------------------------------
    # Fixed species concentrations

    X0 = 100
    X2 = 10
    X3 = 1

    # -----------------------------------------------------------------------------
    # Parameters

    Vf1 = 100.0
    Keq1 = 10.0
    Km1_X0 = 1.0
    Km1_S1 = 1.0

    Vf2 = 50.0
    Keq2 = 10.0
    Km2_S1 = 1.0
    Km2_X2 = 1.0

    Vf3 = 10.0
    Keq3 = 10.0
    Km3_S1 = 1.0
    Km3_X3 = 1.0
    # -----------------------------------------------------------------------------

lin5_hill.psc
^^^^^^^^^^^^^

.. image:: included_files_files/lin5_hill.png

:download:`model <included_files/lin5_hill.psc>`
:download:`layout file <included_files/lin5_hill_layout.dict>`

Example Notebooks
-----------------