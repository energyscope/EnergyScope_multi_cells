Overview
++++++++
.. _label_sec_overview:


:Version: |version| (|release|)
:Date: |today|
:Version main developer: Paolo Thiran (UCLouvain)
:Short summary: Mulit-regional *whole*-energy system with an hourly resolution and data for the European energy system in 2035.

The EnergyScope Multi-Cells model optimises for multiple interconnected regions the design and operation of all the energy sectors, with the same level of details. The energy sectors are defined as electricity, heat, mobility and non-energy demand. 


The EnergyScope models suite is developped through a collaboration between UCLouvain (Belgium) and EPFL (Switerland). 
It was originally created by EPFL (Switzerland) since 2011. The EnergyScope Multi-Cells model is one specific instance of the EnergyScope suite, tailored for multi-regional energy systems.

The linear programming model is written in algebraic language using AMPL. This AMPL code is englobed into a python package that pre-processes the data, runs the optimisation and post-processes the data.

Features
========

In the energy system community, several criteria are used to compare models. 
The EnergyScope TD is a bottom-up energy system model and has been compared to 53 other models in :cite:`Limpens2021thesis`. The EnergyScope Multi-Cells model features the same characteristics and advantages. It goes even furter into the whole-energy system appraoch by adding shipping and aviation to the energy demands. The main difference with the original EnergyScope model is the multi-regional formulation. However, this improvement leads to a longer computational time.   

Each model is tailored for a different applications. In the following, the strengths and weaknesses of the model is presented.


Strengths of the model
----------------------


Whole energy system
^^^^^^^^^^^^^^^^^^^


The current version of the energy system represents all the energy sectors of the European energy system. 
The sectors are coupled, in the sence that electricity can be used for other sectors, such as heat or mobility. 
:numref:`Figure %s <fig:esmc_eu_illustration>` shows the energy system implemented in the model, it accounts for :

- 28 energy carriers
- 167 technologies
- 17 end use layers

In its multi-regional implementation, the model also follows the whole-energy system appraoch and considers eight different energy carriers for energy exchanges between regions. This characteristic contrasts with other multi-regional models that often considers only electricity or electricity and hydrogen as energy carriers. 


.. figure:: /images/esmc_eu_illustration.png
   :alt: Illustrative example of a EnergyScope Multi-Cells implementation.
   :name: fig:esmc_eu_illustration
   :width: 16cm

   The European energy system modelled with EnergyScope Multi-Cells implements in each country: 
   28 energy resources converted through 167 technologies to supply demands in 17 end-use layers. 
   Technologies (in bold) represent groups of technologies with different energy inputs 
   (e.g. Boilers include methane boilers, oil boilers ...).
   Abbreviations: atmospheric (Atm.), battery electric vehicle (BEV), biomass (biom.), 
   biomethanisation (Biometh.), compressed air energy storage (CAES), carbon capture (CC), 
   combined cycle gas turbine (CCGT), cogeneration of heat and power (CHP), carbon dioxyde (CO2), 
   collector (Coll.) concentrated solar power (CSP), decentralised heat (Decen. or Dec.), 
   district heating network (DHN), electricity (Elec.), Fischer-Tropsch (FT) geothermal (Geoth.), 
   hydrogen (H2), high-temperature (High T), high value chemical (HVC), internal combustion engine (ICE), 
   industrial (Ind.), low-temperature (Low T), methanation (Methan.), methanolation (Methanol.), 
   offshore (Off.), onshore (On.), power block (PB), plug-in hybrid electric vehicle (PHEV), 
   pumped hydro storage (PHS), photovoltaic (PV), renewable (Re.), thermal (Th.).

Optimisation of hourly operation over a year
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The formulation of the year is based on typical days, which reduces the number of time periods accounted in the model.
However, a reconstruction method enables to capture energy stored at different time scale. :numref:`Figure %s <fig:estd_time_scale>` illustrates the different time scales captured by the model. A validation of this typical days approach and a method to select a priori the number of typical days for a new case study can be found in :cite:`thiran2023validation`.

.. figure:: /images/estd_different_time_scales.png
   :alt: Illustrative example of a decentralised heating layer.
   :name: fig:estd_time_scale
   :width: 16cm

   Illustration of the different time scale optimised by the model. 
   The hourly power balance is resolved on typical days (bottom), 
   while the level of charge of storage is captured at week to seasonal level (middle and top).
   This illustration is for the Swiss case study presented in [limpens2019energyScope].

The model optimises the operation and design, enabling all the differnt configuration to satisfy the imposed demand.


Open source
^^^^^^^^^^^

The model is both open source (github) and documented (this document). 
The choosen plateform foster collaboration and enable several researchers to work together.

Weaknesses of the model
---------------------------

Low technico-economico resolution
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The current implementaion has a low level of technico-economic contraints. 
Technically, the technologies can switch from off to full load in one hour. 
Economically, the operation is related to the resource purchase and the maintenance cost account for the rest. 
The latter is assumed proportional to the capacity installed.


No market equilibrium
^^^^^^^^^^^^^^^^^^^^^

The demand is described by a yearly demand and an hourly profile.
The yearly demand is exogeneous to the problem and inelastic. Thus doesn't result from an offer-demand balance.
In other words, the system is forced to supply the demand even if the cost of the system soars.


Deterministic optimisation
^^^^^^^^^^^^^^^^^^^^^^^^^^

The mathematical model is written as a linear continuous problem. 
Thus, it is resolved by using linear programming solvers which are deterministic optimisation. 
All the information is known *a priori* and the solver reaches a single optimum. 

Moreover, linear programming gives chaotics solution, which can vary from white to black when slighlty changing a parameter.
As an example, one solution could be based on gas cogeneration while another is based on Combined Cycle Gas Turbines.

Uncertainty quantification techniques enable to overcome this issue by running several time the model under different configuration. 
Therefore, a short computaitonal time is required to enable many sampling. This technique has been applied to the Belgian energy system model in :cite:`rixhon2021role`.

Another approach is to explore the near-optimal space. It can be used when the computational time is too large or the charecteristion of the input parameters' uncertainty is not feasible. This is the case with the European version of the model. Thus, an hydrib method combinng scenario analysis and near-optimal exploration was applied to it to generate twelve alternative designs and overcome the deterministic feature of the model.

.. caution::
   cite thesis Paolo Thiran and paper on the Role of Renewable Fuels in a Fossil-free European Energy System.

One year time horizon
^^^^^^^^^^^^^^^^^^^^^

EnergyScope Multi-Cells is a snapshot model, in the sence that it represents the energy system in a target future year, without considering existing system.




