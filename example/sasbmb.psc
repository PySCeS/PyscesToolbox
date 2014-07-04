FIX: A F I


R1:
    A = B
    ((Vf1/Ks1)*(A-B/Keq1)*(A/Ks1 + B/Kp1)**(h1-1))/((A/Ks1 + B/Kp1)**(h1-1) + ((1 + (E/Km1_1)**h1 + (H/Km1_2)**h1)/(1 + a1_1*(E/Km1_1)**h1 + a1_2*(H/Km1_2)**h1)))

R2:
    B = C
    Vf2/Ks2*(B - C/Keq2)/(1 + B/Ks2 + C/Kp2)


R3:
    C = D
    Vf3/Ks3*(C - D/Keq3)/(1 + C/Ks3 + D/Kp3)

R4:
    D = E
    Vf4/Ks4*(D - E/Keq4)/(1 + D/Ks4 + E/Kp4)


R5:
    E = F
    (Vf5*E)/(E + Ks5)


R6:
    C = G
    Vf6/Ks6*(C - G/Keq6)/(1 + C/Ks6 + G/Kp6 + E/Ki6)


R7:
    G = H
    Vf7/Ks7*(G - H/Keq7)/(1 + G/Ks7 + H/Kp7)

R8:
    H = I
    (Vf8*H)/(H + Ks8)


A = 15
F = 10

I = 10

B=0
C=0
D=0
E=0
G=0
H=0


Vf1   = 100
Keq1  = 5
Ks1   = 7
Kp1   = 1000
Km1_1 = 3
Km1_2 = 40
a1_1  = 0.01
a1_2  = 100
h1    = 4

Vf2  = 100
Keq2 = 50
Ks2  = 10
Kp2  = 100

Vf3  = 35
Keq3 = 10
Ks3  = 10
Kp3  = 100

Vf4  = 100
Keq4 = 100
Ks4  = 10
Kp4  = 100

Vf5 = 40
Ks5 = 5


Vf6 = 35
Keq6= 100
Ks6 = 5
Kp6 = 50
Ki6 = 10

Vf7= 100
Keq7= 10
Ks7= 10
Kp7= 100

Vf8= 50
Ks8= 5




