Data for the Belgian energy system
++++++++++++++++++++++++++++++++++

This version of the model has minor improvments compared to EnergyScope v2.1 [GL thesis].
The documentation is available in Appendix C of `Thesis <https://www.researchgate.net/profile/Gauthier-Limpens/publication/352877189_Generating_energy_transition_pathways_application_to_Belgium/links/60dd7713458515d6fbef9700/Generating-energy-transition-pathways-application-to-Belgium.pdf>`_ 
However, some changes have been made and are detailed hereafter.

Non-energy demand implementation
--------------------------------

Non energy demand represents the use of energy carriers as feedstocks. The best examples are plastics and fertilisers. 
The first uses hydrocarbons as material, the second require ammonia, which is produced from natural gas (steam methan reforming and then haber-bosch).

While the former version proposes the implementation of final energy demand (i.e. hydrocarbons or natural gas) for the non-energy demand, this version proposes the use of three end-use demand.
Based on the works of Rixhon et al. [rixhon2021comprehensive], the NED accounts for three types of end use demand: ammonia, methanol and high-value chemicals (HVC).
Thus, the conversion pathways to produce all these feedstocks were implemented.

The following figure represents the different conversion pathways. The new resources, technologies and end-use demand are represented.
Hereafter, we detail the characteristics for each technologies:

.. image:: /images/NED_v2.2.png

In 2015, the NED (in TWh) was split in 77.9% of HVC, 19.2% of ammonia and 2.9% of methanol. We suppose these shares to be constant during the transition.
The Non-energy demand in 2035 for the NED is 53 109 GWh


Resources updated:
------------------

In this version, some fuels have been added and the projection prices of renewable fuels in 2035 have been updated. 


New fuels:
~~~~~~~~~~

They are: Ammonia, Ammonia_re, Methanol, Methanol_re, h2, h2_re

To avoid ambiguity between renewable fuels and their fossil equivalent, the ambiguous resources are followeb by '_re' if they are issued from renewable feedstocks.
Thus, we have gas and gas_re, or h2 and h2_re. Gas refers to what is usually called 'natural gas', while gas_re refers to methane from biogas, methanation of renewable hydrogen,...


Renewable fuels prices:
~~~~~~~~~~~~~~~~~~~~~~~

The estimation of previous fuels price were made based on the works of Brynolf et al. [BRYNOLF] in 2018. Since, a specific study for the Belgian case has been conducted by a consortium of industries [H2coalitie], which estimate new prices for the imports.
The following table summarise all the input data for the resources (update of Table C.2 in `Thesis <https://www.researchgate.net/profile/Gauthier-Limpens/publication/352877189_Generating_energy_transition_pathways_application_to_Belgium/links/60dd7713458515d6fbef9700/Generating-energy-transition-pathways-application-to-Belgium.pdf>`_ ).


.. csv-table:: Resources prices:  
    :header: Resource, availability,  global warming potential, price
    :widths: 15 10 30 10

    ,``avail``,``gwp_op``,``c_op``
    , [GWh/y], [kt_CO2eq/GWh], [M€_2015/GWh]
    Electricity imported,27568,0.206,0.084
    Gasoline,Infinity,0.345,0.082
    Diesel,Infinity,0.315,0.080
    Bio-ethanol,Infinity,0,0.111
    Bio-diesel,Infinity,0,0.120
    Light fuel oil,Infinity,0.312,0.060
    Gas (fossil),Infinity,0.267,0.044
    Gas (renewable),Infinity,0,0.118
    Wood,23400,0.012,0.033
    Wet biomass,38900,0.012,0.006
    Coal,33355,0.401,0.018
    Uranium,Infinity,0.004,0.004
    Waste,17800,0.150,0.023
    Hydrogen (fossil),Infinity,0.364,0.088
    Hydrogen (renewable),Infinity,0,0.119
    Ammonia (fossil),Infinity,0.285,0.076
    Methanol (fossil),Infinity,0.350,0.082
    Ammonia (renewable),Infinity,0,0.082
    Methanol (renewable),Infinity,0,0.111  



Technologies updates:
---------------------

New technologies have been added, related to the new fuels.
As an example, methanol can now be used for cars or trucks. 
These new technologies have no restriction of deployment.

The offshore wind capacity has been increased from 3.5 to 6 GW due to recent annoucement of the  
`Belgian offshore plateform <https://www.belgianoffshoreplatform.be/fr/>`_ .

Bibliography:
-------------

- [1] Limpens, G. (2021). Generating energy transition pathways: application to Belgium (Doctoral dissertation, UCL-Université Catholique de Louvain).
- [2] Rixhon, Xavier and Colla, Martin and Verleysen, Kevin and Tonelli, Davide and Limpens, Gauthier. Comprehensive integration of the non-energy demand within a whole-energy system : Towards a defossilisation of the chemical industry in Belgium. Proceedings ECOS2021.
- [3] Brynolf, S., Taljegard, M., Grahn, M., & Hansson, J. (2018). Electrofuels for the transport sector: A review of production costs. Renewable and Sustainable Energy Reviews, 81, 1887-1905. 
- [4] Hydrogen Import Coalition. Shipping sun and wind to Belgium is key in climate neutral economy. 2020