.. _ch_esmc:

Model formulation
=================

.. caution ::
   TO BE UPDATED TO MULTI-CELLS version

.. role:: raw-latex(raw)
   :format: latex
..




Overview
--------

The modelling with EnergyScope Multi-Cells is done in two steps; see :numref:`Figure %s <fig:model_overview_blank>`. First, a generic energy systm optimisation model is developed such
that it can be used with any multi-regional whole-energy system (middle block in :numref:`Figure %s <fig:model_overview_blank>`). This part is described in this Section. Then, the energy background of the specific case study is modelled (left block in :numref:`Figure %s <fig:model_overview_blank>`). In this documentation, the modelling of a fossil-free European energy system is described in the Section :doc:`/sections/Input data`. Other implementations are possible. For instance, the model has
already been used to model Italy divided into three main regions :cite:`thiran2021flexibility` and to model Western Europe into six macro-regions :cite:`cornet2021energy,thiran2023validation`. The model gives as an output and energy strategy for the regions modelled. For each regions, it provides an energy system with its cost, emissions, installed capacitites and hourly operation. Between regions, it defines the transmission networks to install and the hourly energy exchanges.

.. figure:: /images/model_formulation/model_overview_blank.jpg
   :alt: Overview of the LP modeling framework
   :name: fig:model_overview_blank
   :width: 18cm

   Overview of the energy system modelling framework.


Due to computational restrictions, energy system models rarely optimise
the 8760h of the year. As an example, running the regional EnergyScope model with 8760h time
series takes more than 19 hours; while the hereafter presented
methodology needs approximately 1 minute. A typical solution is to use a
subset of representative days called Typical Days (TDs); this is a trade-off between
introducing an approximation error in the representation of the energy
system (especially for short-term dynamics) and computational time. Thus, as in the original EnergyScope TD model, the optimisaiton of the enrgy system is done in two steps, see :numref:`Figure %s <fig:ProcessStructure>`:

-  the first step consists in pre-processing the time series and solving
   a MILP problem to determine the adequate set of TDs, see Section :ref:`sec_td_selection`.

-  the second step is the main energy model: it identifies the optimal
   design and operation of the energy system, i.e. technology selection, sizing and operation
   for a target future year, see Section :ref:`sec_estd`.

These two steps can be computed independently. Usually, the first step
is computed once for an energy system with given weather data whereas
the second step is computed several times (once for each different
scenario).

.. figure:: /images/model_formulation/meth_process_structure.png
   :alt: Overview of the EnergyScope TD framework in two-steps.
   :name: fig:ProcessStructure
   :width: 18cm
   
   Overview of the EnergyScope TD framework in two-steps. **STEP 1**: 
   optimal selection of typical days (Section :ref:`sec_td_selection`). **STEP 2**: 
   Energy system model (Section :ref:`sec_estd`). The first step processes 
   only a subset of parameters, which account for the 8760h time series. 
   Abbreviations: TD, MILP, LP and GWP



This documentation is built from previous works :cite:`Moret2017PhDThesis,Limpens2019,Limpens2021thesis`. 
For more details about the research approach, the choice of clustering method or the reconstruction method; refer to :cite:`Limpens2021thesis, thiran2023validation`.


.. _sec_td_selection:

Typical days selection
----------------------

Resorting to TDs has the main advantage of reducing the computational
time by several orders of magnitude. Usually, studies use between 6 and
20 TDs 
:cite:`Gabrielli2018,Despres2017,Nahmmacher2014,Pina2013`
sometimes even less
:cite:`Poncelet2017,Dominguez-Munoz2011`. 

Clustering method
~~~~~~~~~~~~~~~~~

We use the k-medoid algorithm developed by Dominguez-Muños et al. :cite:`Dominguez-Munoz2011` to cluster the TDs.
Limpens et al. :cite:`Limpens2019` have compared several algorithms for this typology of problem and
have chosen the one of Dominguez-Muños et al. It has a simple mixed-integer programming formulation,
fast convergence and low error on both time series and duration curves. In this algorithm, the days are grouped into clusters to minimise the
intra-cluster distance, and the medoid of the cluster is taken as TD. The distance between
(:math:`Dist`) between 2 days (:math:`i` and :math:`j`), the L1 norms between each hour (:math:`h`) for the time series (:math:`ts`)
representing each attribute (:math:`a`) are summed over the 24 hours of the day. This gives the distance
for each attribute. Then, a weighted sum (with weight, :math:`\omega_a`) of these distances is computed.
The number of attributes corresponds to the number of time series considered multiplied
by the number of regions studied.


.. math::
    Dist(i,j)\ =\ \sum_{a\in A}\omega_a \sum_{h=1}^{24}|ts(a,h,i)-ts(a,h,j)|.
    :label: eq:dist

The weights are defined to reflect the importance of each attribute in the energy system: (i) only the
attributes with different time series between the different days are considered. For instance,
in this model, the freight is considered constant over the entire year, and the public mobility
has the same time series for each day of the year. Hence, they are not considered for the
TDs clustering; (ii) the sum of the weights of the different attributes is equal to 1 with 0.5 for
the attributes defining the variable demand and 0.5 for the attributes defining the variable
production; (iii) among the variable demands, the weight is split according to the total
demand over the year, considering Carnot coefficient of performance to scale space heating
and space cooling demands; and (iv) among the variable productions, the weight is split
according to their yearly production at full potential deployment.

The clustering algorithmselects the same days as TDs for all the regions.
As these days have different time series in different regions, it ensures the temporal
synchronicity of the different regions while considering the spatial disparity of demands
and productions. Hence, the TDs selection considers both the intra- and inter-regional
relations among the time series. In addition to the clustering algorithm, preprocessing and
postprocessing of the time series are performed. During the preprocessing, the time series
are normalised such that their sum over the year is equal to 1, while in the postprocessing,
the time series of the TDs are rescaled to preserve the average value over the year.


Implementing seasonality with typical days
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Using TDs can introduce some limitations. As an example, traditionally,
model based on TDs are not able to include inter-days or seasonal
storage due to the discontinuity between the selected days. Thus, they
assess only the capacity of production without accounting for storage
capacities. Carbon-neutral energy system will require long term storage
and thus, this limitation must be overcome. Therefore, we implemented a
method proposed by :cite:t:`Gabrielli2018` to rebuild a year
based on the typical days by defining a sequence of typical days. This allows to
optimise the storage level of charge over the 8760h of the year.
:cite:t:`Gabrielli2018` assigned a TD to each day of the
year; all decision variables are optimised over the TDs, apart from the
amount of energy stored, which is optimised over 8760h. This methodology 
is illustrated in the following :numref:`Figure %s <fig:SeasonalityImplementation>`.


.. figure:: /images/model_formulation/gabrielli.png
   :alt: Illustration of the typical days reconstruction method 
   :name: fig:SeasonalityImplementation
   :width: 14cm
   
   Illustration of the typical days reconstruction method proposed by
   :cite:`Gabrielli2018` over a week. The example is based
   on 3 TDs: TD 1 represents a cloudy weekday, applied to Monday,
   Thursday and Friday; TD 2 is a sunny weekday, applied to Tuesday and
   Wednesday; and TD 3 represents sunny weekend days. The power profile
   (above) depends solely on the typical day but the energy stored
   (below) is optimised over the 8760 hours of the year (blue curve).
   Note that the level of charge is not the same at the beginning
   (Monday 1 am) and at the end of the week (Sunday 12 pm).

The performances of this method has been quantified in a previous works for the regional model :cite:`Limpens2019`, and for the multi-regional model :cite:`thiran2023validation`.
A general a priori method to select the number of typical days for a new case study is proposed in :cite:`thiran2023validation`.
This work shows that the time series error due to the use of TDs is larger and proportional to the design error on the energy system.
Hence, the time series error can be used to select the number of typical days.
For the Belgian region case, 12 TDs is the best trade-off. For the 34-regions European case, 16 TDs are chosen.

.. _sec_estd:

Energy system model
-------------------


Hereafter, we present the core of the energy model. First, we introduce
the conceptual modelling framework with an illustrative example, in
order to clarify as well the nomenclature. Second, we introduce the
constraints of the energy model (data used are detailed in
the Section :doc:`/sections/Input data`).


.. _ssec_lp_framework:

Linear programming formulation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


The model is mathematically formulated as a LP problem
:cite:`fourer1990modeling`. 
:numref:`Figure %s <fig:linear_programming_example>` represents - in a simple
manner - what is a LP problem and the nomenclature used. In
capital letters, :math:`\text{SETS}` are collections of distinct items (as in the
mathematical definition), e.g. the :math:`\text{RESOURCES}` set regroups all the
available resources (DIESEL, WOOD, etc.). In italic lowercase letters,
:math:`parameters` are known values (inputs) of the model, such as the demand
or the resource availability. In bold with first letter in uppercase,
**Variables** are unknown values of the model, such as the installed
capacity of PV. These values are determined (optimised) by the solver
within an upper and a lower bound (both being parameters). As an
example, the installed capacity of wind turbines is a decision variable;
this quantity is bounded between the already installed capacity and the maximum available
potential. *Decision variables* can be split in two categories:
independent decision variables, which can be freely fixed, and dependent
decision variables, which are linked via equality constraints to the
previous ones. As an example the investment cost for wind turbines is a
variable but it directly depends on the number of wind turbines, which
is an independent decision variable. **Constraints** are inequality or
equality restrictions that must be satisfied. The problem is subject to
(*s.t.*) constraints that can enforce, for example, an upper limit for
the availability of resources, energy or mass balance, etc. Finally, the
**Objective function** is a particular constraint whose value is to be
maximised (or minimised).

.. figure:: /images/model_formulation/chp_estd_lp_conceptual.png
   :alt: Conceptual illustration of a LP problem.
   :name: fig:linear_programming_example
   :width: 14cm

   Conceptual illustration of a LP problem and the nomenclature used.
   Symbol description: maximum installed size of a technology
   (:math:`f_{max}`), installed capacity of a technology (**F**) and total
   system cost (:math:`\textbf{C}_{\textbf{tot}}`). In this example, a specific technology (**F**
   [*’PV’*]) has been chosen from the set *TECHNOLOGIES*.


.. _ssec_conceptual_modelling_framework:

Conceptual modelling framework
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The proposed modelling framework for one region is a simplified representation of an
energy system accounting for the energy flows within its boundaries. Its
primary objective is to satisfy the energy balance constraints, meaning
that the demand is known and the supply has to meet it. In the energy
modelling practice, the energy demand is often expressed in terms of final energy consumption (FEC).
According to the definition of the European commission, FEC is
defined as “*the energy which reaches the final consumer’s door*”
:cite:`EU_FEC`. In other words, the FEC is the amount of
input energy needed to satisfy the end-use demand (EUD) in energy services. As an
example, in the case of decentralised heat production with a methane boiler,
the FEC is the amount of methane consumed by the boiler; the EUD is the
amount of heat produced by the boiler, i.e. the heating service needed
by the final user.

The input for the proposed modelling framework is the EUD in energy
services, represented as the sum of four energy-sectors: electricity,
heating, mobility and non-energy demand; this replaces the classical
economic-sector based representation of energy demand. Heat is divided
in three end-use types (EUTs): high temperature heat for industry, low temperature for
space heating and low temperature for hot water. Mobility is divided in
four EUTs: passenger mobility, long-haul aviation, freight and shipping [1]_. Non-energy demand is,
based on the IEA definition, “*fuels that are used as raw materials in
the different sectors and are not consumed as a fuel or transformed into
another fuel.*” :cite:`IEA_websiteDefinition`. As examples,
the European Commission includes as non-energy the following materials:
“*chemical feed-stocks, lubricants and asphalt for road construction.*”
:cite:`EuropeanCommission2016`.

A simplified conceptual example of the energy system structure is
proposed in  :numref:`Figure %s <fig:conceptual_example>`. The system is
split in three parts: resources, energy conversion and demand. In this
illustrative example, resources are solar energy, electricity and fossil gas.
The EUD are electricity, space heating and passenger mobility. The
energy system encompasses all the energy conversion technologies needed
to transform resources and supply the EUD. In this example, Solar and fossil gas
resources cannot be directly used to supply heat. Thus, they use
technologies, such as boilers or combined heat and power (CHP) for fossil gas, to supply the EUT layer
(e.g. the high temperature industrial heat layer). *Layers* are defined
as all the elements in the system that need to be balanced in each time
period; they include resources and EUTs. As an example, the electricity
layer must be balanced at any time, meaning that the production and
storage must equal the consumption and losses. These layers are
connected to each other by *technologies*. We define three types of
technologies: *technologies of end-use type*, *storage technologies* and
*infrastructure technologies*. A technology of end-use type can convert
the energy (e.g. a fuel resource) from one layer to an EUT layer, such
as a CHP unit that converts fossil gas into heat and electricity. A storage
technology converts energy from a layer to the same one, such as thermal storage that
stores heat to provide heat. In this example (
:numref:`Figure %s <fig:conceptual_example>`), there are two storage technologies:
thermal storage for heat and pumped hydro storage (PHS) for electricity. An infrastructure technology
gathers the remaining technologies, including the networks, such as the
power grid and DHNs, but also technologies linking non end-use layers,
such as methane production from wood gasification or hydrogen production
from methane reforming.

.. figure:: /images/model_formulation/chp_estd_conceptual_framework.png
   :alt: Conceptual example of an energy system.
   :name: fig:conceptual_example
   :width: 12cm

   Conceptual example of an energy system with 3 resources, 8
   technologies (of which 2 storages (in colored oval) and 1
   infrastructure (grey rectangle)) and 3 end use demands.
   Abbreviations: PHS, electrical heat pump (eHP), CHP, CNG. Some icons
   from :cite:`FlatIcon`.

:numref:`Figure %s <fig:conceptual_example>` illustrates with the same conceptual example the extension of EnergyScope TD
to EnergyScope Multi-Cells. This extension adds the possibility of representing different regions, also called cells.
Each cell is considered as one node with its own energy demand, resources and energy conversion system.
At each node, the energy balance for each energy carrier is ensured for all time steps,
and each cell can exchange different energy carriers with other cells.
As the model is developed into a whole-energy system perspective, electricity is not
the only carrier considered for energy exchanges between regions. 
The model is designed to consider also other types of energy carriers such as gaseous and liquid fuels. Some
are transported through networks (e.g. electricity, methane or hydrogen), and others are
transported through freight (e.g. ammonia, methanol or woody biomass). Both the quantity
exchanged and the interconnector sizes, or the freight needed to transport these resources,
are optimised by the model.

.. figure:: /images/model_formulation/esmc_concept.jpg
   :alt: Conceptual example of the extension of EnergyScope to EnergyScope Multi-Cells.
   :name: fig:esmc_concept
   :width: 18cm

   Conceptual example of an energy system modelled with EnergyScope TD and
   extension to EnergyScope Multi-Cells.
   Abbreviations: combined heat and power (CHP), compressed natural gas (CNG), electrical heat pump (eHP), gigawatt
   (GW), pumped hydro storage (PHS), passenger-kilometre (pkm). Some icons
   from :cite:`FlatIcon`. Adapted from :cite:`Limpens2019`.


The energy system is formulated as a linea programming problem.
The model optimises the design of the energy system to meet the energy demand at each
hour and minimise the total annual cost of the overall system. In each region, the model
determines each technology’s installed capacity and operation at each hour. Between
regions, the model determines the interconnection installed and the energy exchanged in
each period.

In the following, we present the
complete formulation of the model in two parts. First, all the terms
used are summarised in several tables.
Then, the equations representing the **Constraints** and the **Objective
function** are formulated and described in the following paragraphs.

.. _ssec_sets_params_vars:

Sets, parameters and variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tables :numref:`%s <tab:sets_1>` and :numref:`%s <tab:sets_2>` list and describe the :math:`\text{SETS}` with their relative indices used in the equations.
Tables :numref:`%s <tab:paramsDistributions>` and :numref:`%s <tab:params>` list and describe the model :math:`parameters`.
Tables :numref:`%s <tab:variablesIndependent>` and
:numref:`%s <tab:variablesdependent>` list and describe the independent and dependent Variables, respectively.


.. csv-table:: List of sets and subsets related to the spatial and temporal part of the optimisation problem with their index. The set name is as close as possible to the name in the code. The index is the short name on which we index the equations in this document. It is used in capital letters when it points to the entire set and in lowercase letters when it points to each set instance.
   :header: Set group, Set name,Index,Description
   :widths: 15,20,10,55
   :name: tab:sets_1

    **Regions**, *REGIONS*, *REG*, Regions
    , *RWITHOUTDAM*, \-, Subset of regions without hydro dams
    **Periods**, *PERIODS*, *T*, Timpe periods of the year [a]_
    , *HOURS*, *H*, Hourds of the day
    , *TYPICAL_DAYS*, *TD*, Typical days
.. [a]
   As the model uses typical days, a mapping is necessary to go from hourly data on typical days to hourly
   data over the entire year. In the equations, thismapping is noted as :math:`t (h, td) \in T`.


.. csv-table:: List of sets and subsets related to demands, resources and technologies with their index. The set name is as close as possible to the name in the code. The index is the short name on which we index the equations in this document. It is used in capital letters when it points to the entire set and in lowercase letters when it points to each set instance.
   :header: Set group, Set name,Index,Description
   :widths: 15,20,10,55
   :name: tab:sets_2

   **Demands**, *SECTORS*, *S*, Sectors of the energy system
   , *END_USES_INPUT*, *EUI*, EUD inputs to the model
   , *END_USES_TYPES*, *EUT*, EUD types in the model
   , *END_USES_CATEGORIES*, *EUC*, EUD categories
   , *EUT_OF_EUC(euc)*, *EUT_OF_EUC(euc)*, Subsuts of EUD types regrouped into categories
   **Resources**, *RESOURCES*, *RES*, Energy resources
   , *RE_RESOURCES*, *RESre*, Subset grouping renewable resources
   , *RES_IMPORT_CONSTANT*, *REScst*, Subset grouping resources with a constant import over the year
   , *EXCHANGE_R*, *ER*, Subsut of resources considered for energy exchanges
   , *NOEXCHANGES*, *NOEXCHANGES*, Subset of resources not considered for exhcnages
   , *EXCHANGE_NETWORK_R*, *NER*, Subset of *ER* for resources exchanged through a network
   , *EXCHANGE_FREIGHT_R*, *FER*, Subset of *ER* for resources exchanged through freight
   **Layers**, *LAYERS* , *L*, Set of layers balanced at each time step regroups EUT and RES
   **Technologies**, *TECHNOLOGIES*, *TECH*, Technologies
   , *TECH_OF_EUC(euc)*, *TECH_OF_EUC(euc)*, Subsets of technologies supplying each EUD category
   , *TECH_OF_EUT(eut)*, *TECH_OF_EUT(eut)*, Subsets of technologies supplying each EUD type
   , *STORAGE_TECH*, *STO*, Subset grouping the storage technologies
   , *STORAGE_DAILY*, *STO_DAILY*, Subset of daily storage technologies
   , *STO_OF_EUT(eut)*, *STO_OF_EUT(eut)*, Subset of storage technologies related to each EUD type
   , *TS_OF_DEC_TECH(tech)*, *TS_OF_DEC_TECH(tech)*, Subset of thermal storage technologies linked with each decentralised heating technology 
   , *V2G*, *V2G*, Subset of electricvehicles (EVs) which can be used for vehicle-to-grid (V2G)
   , *EVs_BATT*, *EVs_BATT*, Set of batteries of EVs
   , *EVs_BATT_OF_V2G*, *EVs_BATT_OF_V2G*, Set linking Evs batteries with their EVs
   , *NETWORK_TYPE(ner)*, *NT(ner)*, Subset of network types for each resource exchanges through networks


.. container::

   .. table:: Time series parameters
      :name: tab:paramsDistributions

      +----------------------------------+-----------+-----------------------------+
      | **Parameter**                    | **Units** | **Description**             |
      +==================================+===========+=============================+
      | :math:`\%_{elec}(reg, h, td)`    | [-]       | Yearly time series          |
      |                                  |           | (adding up to 1) of         |
      |                                  |           | electricity end-uses        |
      +----------------------------------+-----------+-----------------------------+
      | :math:`\%_{sh}(reg, h, td)`      | [-]       | Yearly time series          |
      |                                  |           | (adding up to 1) of         |
      |                                  |           | space heating (SH) end-uses |
      +----------------------------------+-----------+-----------------------------+
      | :math:`\%_{sc}(reg, h, td)`      | [-]       | Yearly time series          |
      |                                  |           | (adding up to 1) of         |
      |                                  |           | space cooling (SC) end-uses |
      +----------------------------------+-----------+-----------------------------+
      | :math:`\%_{pass}(reg, h, td)`    | [-]       | Yearly time series          |
      |                                  |           | (adding up to 1) of         |
      |                                  |           | passenger mobility          |
      |                                  |           | end-uses                    |
      +----------------------------------+-----------+-----------------------------+
      | :math:`\%_{fr}(reg, h, td)`      | [-]       | Yearly time series          |
      |                                  |           | (adding up to 1) of         |
      |                                  |           | freight mobility end-uses   |
      +----------------------------------+-----------+-----------------------------+
      | :math:`c_{p,t}(tech, reg, h, td)`| [-]       | Hourly maximum capacity     |
      |                                  |           | factor for each             |
      |                                  |           | technology (default 1)      |
      +----------------------------------+-----------+-----------------------------+
      | :math:`soc_{ev}(v2g, h)`         | [-]       | Minimum state of charge     |
      |                                  |           | of EVs battery              |
      |                                  |           | at each hour of the day     |
      +----------------------------------+-----------+-----------------------------+


.. container::

   .. table:: List of parameters (except time series).
      :name: tab:params

      +----------------------+----------------------+-----------------------+
      | Parameter            | Units                | Description           |
      +======================+======================+=======================+
      | :math:`\tau\         | [-]                  | Investment cost       |
      | (reg, tech)`         |                      | annualization factor  |
      +----------------------+----------------------+-----------------------+
      | :math:`i_{rate}`     | [-]                  | Real discount rate    |
      +----------------------+----------------------+-----------------------+
      | :math:`endUses_      | [GWh/y] [b]_         | Annual end-uses in    |
      | {year}               |                      | energy services per   |
      | (reg, eui, s)`       |                      | sector                |
      +----------------------+----------------------+-----------------------+
      | :math:`endUsesInput  | [GWh/y] [b]_         | Total annual          |
      | (reg, eui)`          |                      | end-uses in energy    |
      |                      |                      | services              |
      +----------------------+----------------------+-----------------------+
      | :math:`f_{min},      | [GW] [c]_ [d]_       | Min./max. installed   |
      | f_{max}              |                      | size of the           |
      | (reg, tech)`         |                      | technology            |
      +----------------------+----------------------+-----------------------+
      | :math:`f_{min,\%},   | [-]                  | Min./max. relative    |
      | f_{max,\%}           |                      | share of a            |
      | (reg, tech)`         |                      | technology in a       |
      |                      |                      | layer                 |
      +----------------------+----------------------+-----------------------+
      | :math:`avail_{local} | [GWh/y]              | Resource yearly total |
      | (reg, res)`          |                      | local availability    |
      |                      |                      | in each region        |
      +----------------------+----------------------+-----------------------+
      | :math:`avail_{ext}   | [GWh/y]              | Resource yearly total |
      | (reg, res)`          |                      | availability for      |
      |                      |                      | import from the       |
      |                      |                      | exterior of the       |
      |                      |                      | overall system in     |
      |                      |                      | each region           |
      +----------------------+----------------------+-----------------------+
      | :math:`c_{op, local} | [M€\                 | Specific cost of      |
      | (reg, res)`          | :math:`_{2015}`/GWh] | local resources       |
      |                      |                      | in each region        |
      +----------------------+----------------------+-----------------------+
      | :math:`c_{op, ext}   | [M€\                 | Specific cost of      |
      | (res)`               | :math:`_{2015}`/GWh] | resources coming from |
      |                      |                      | the rexterior         |
      +----------------------+----------------------+-----------------------+
      | :math:`veh_{capa}    | [km-pass/h/veh.] [b]_| Mobility capacity     |
      | (tech)`              |                      | per vehicle (veh.).   |
      +----------------------+----------------------+-----------------------+
      | :math:`\%_{          | [-]                  | Ratio peak/max.       |
      | Peak_{sh}} (reg)`    |                      | space heating demand  |
      |                      |                      | in typical days       |
      +----------------------+----------------------+-----------------------+
      | :math:`\%_{          | [-]                  | Ratio peak/max.       |
      | Peak_{sc}} (reg)`    |                      | space cooling demand  |
      |                      |                      | in typical days       |
      +----------------------+----------------------+-----------------------+
      | :math:`f(            | [GW] [d]_            | Input from (<0) or    |
      | res\cup tech         |                      | output to (>0) layers |
      | \setminus sto, l)`   |                      | . f(i,j) = 1 if j is  |
      |                      |                      | main output layer for |
      |                      |                      | technology/resource   |
      |                      |                      | i.                    |
      +----------------------+----------------------+-----------------------+
      | :math:`c_            | [M€\ :math:`_{2015}` | Technology specific   |
      | {inv}(reg, tech)`    | /GW] [c]_ [d]_       | investment cost       |
      +----------------------+----------------------+-----------------------+
      | :math:`c_{maint}     | [M€\ :math:`_{2015}` | Technology specific   |
      | (reg, tech)`         | /GW/y]               | yearly maintenance    |
      |                      | [c]_ [d]_            | cost                  |
      +----------------------+----------------------+-----------------------+
      | :math:`{             | [y]                  | Technology lifetime   |
      | lifetime}(reg, tech)`|                      |                       |
      +----------------------+----------------------+-----------------------+
      | :math:`gwp_{constr}  | [ktCO\               | Technology            |
      | (reg, tech)`         | :math:`_2`-eq./GW]   | construction          |
      |                      | [c]_ [d]_            | specific GHG          |
      |                      |                      | emissions             |
      +----------------------+----------------------+-----------------------+
      | :math:`gwp_          | [ktCO\               | Specific GHG          |
      | {op, local}          | :math:`_2`-eq./GWh]  | emissions of local    |
      | (reg, res)`          |                      | resources             |
      +----------------------+----------------------+-----------------------+
      | :math:`re_{share}    | [-]                  | Minimum share [0;1]   |
      | (reg)`               |                      | of primary renewable  |
      |                      |                      | energy (RE)           |
      +----------------------+----------------------+-----------------------+
      | :math:`gwp           | [ktCO\               | Higher                |
      | _{limit}(reg)`       | :math:`_{2-eq}`/y]   | CO\ :math:`_{2-eq}`   |
      |                      |                      | emissions limit       |
      |                      |                      | for each region       |
      +----------------------+----------------------+-----------------------+
      | :math:`gwp           | [ktCO\               | Higher                |
      | _{limit, overall}`   | :math:`_{2-eq}`/y]   | CO\ :math:`_{2-eq}`   |
      |                      |                      | emissions limit       |
      |                      |                      | for the overall system|
      +----------------------+----------------------+-----------------------+
      | :math:`\%_           | [-]                  | Lower and upper       |
      | {public,min}(reg),   |                      | limit to              |
      | \%_{public,max}(reg)`|                      | :math:`\textbf{%}_    |
      |                      |                      | {\textbf{Public}}`    |
      +----------------------+----------------------+-----------------------+
      | :math:`\%_           | [-]                  | Lower and upper       |
      | {av,short,min}(reg), |                      | limit to              |
      | \%_{av,short,max}    |                      | :math:`\textbf{%}_    |
      | (reg)`               |                      | {\textbf{Av,Short}}`  |
      +----------------------+----------------------+-----------------------+
      | :math:`\%_           | [-]                  | Lower and upper       |
      | {fr,rail,min}(reg),  |                      | limit to              |
      | \%_{fr,rail,max}     |                      | :math:`\textbf{%}_    |
      | (reg)`               |                      | {\textbf{Fr,Rail}}`   |
      +----------------------+----------------------+-----------------------+
      | :math:`\%_           | [-]                  | Lower and upper       |
      | {fr,boat,min}(reg),  |                      | limit to              |
      | \%_{fr,boat,max}     |                      | :math:`\textbf{%}_    |
      | (reg)`               |                      | {\textbf{Fr,Boat}}`   |
      +----------------------+----------------------+-----------------------+
      | :math:`\%_           | [-]                  | Lower and upper       |
      | {fr,road,min}(reg),  |                      | limit to              |
      | \%_{fr,road,max}     |                      | :math:`\textbf{%}_    |
      | (reg)`               |                      | {\textbf{Fr,Road}}`   |
      +----------------------+----------------------+-----------------------+
      | :math:`\%_           | [-]                  | Lower and upper       |
      | {dhn,min}(reg),      |                      | limit to              |
      | \%_{dhn,max}(reg)`   |                      | :math:`\textbf{%}_    |
      |                      |                      | {\textbf{Dhn}}`       |
      +----------------------+----------------------+-----------------------+
      | :math:`\%_           | [-]                  | Share of the different|
      | {ned}(reg,           |                      | feedstocks for the    |
      | eut\_of\_euc(NED))`  |                      | non-energy demand     |
      |                      |                      | (NED)                 |
      +----------------------+----------------------+-----------------------+
      | :math:`t_            | [h]                  | Time period duration  |
      | {op}(h,td)`          |                      | (default 1h)          |
      +----------------------+----------------------+-----------------------+
      | :math:`gwp_          | [ktCO\               | Specific GHG          |
      | {op, ext}            | :math:`_2`-eq./GWh]  | emissions of resources|
      | (res)`               |                      | from the exterior     |
      +----------------------+----------------------+-----------------------+
      | :math:`co2_          | [ktCO\               | Specific net GHG      |
      | {net}(res)`          | :math:`_2`-eq./GWh]  | emissions resources   |
      +----------------------+----------------------+-----------------------+     
      | :math:`c_{p}         | [-]                  | Yearly capacity       |
      | (reg, tech)`         |                      | factor                |
      +----------------------+----------------------+-----------------------+
      | :math:`\eta_{s       | [-]                  | Efficiency [0;1] of   |
      | to,in},\eta_{sto     |                      | storage input from/   |
      | ,out} (sto,l)`       |                      | output to layer. Set  |
      |                      |                      | to 0 if storage not   |
      |                      |                      | related to layer      |
      +----------------------+----------------------+-----------------------+
      | :math:`\%_{          | [1/h]                | Losses in storage     |
      | sto_{loss}}(sto)`    |                      | (self discharge)      |
      |                      |                      |                       |
      +----------------------+----------------------+-----------------------+
      | :math:`t_{sto_{in}}  | [-]                  | Time to charge        |
      | (reg, sto)`          |                      | storage (Energy to    |
      |                      |                      | power ratio)          |
      +----------------------+----------------------+-----------------------+
      | :math:`t_{sto_{out}} | [-]                  | Time to discharge     |
      | (reg, sto)`          |                      | storage (Energy to    |
      |                      |                      | power ratio)          |
      +----------------------+----------------------+-----------------------+
      | :math:`\%_           | [-]                  | Storage technology    |
      | {sto_{avail}}        |                      | availability to       |
      | (sto)`               |                      | charge/discharge      |
      +----------------------+----------------------+-----------------------+
      | :math:`\%_{net_      | [-]                  | Losses coefficient    |
      | {loss}}(eut)`        |                      | :math:`[0;1]` in the  |
      |                      |                      | networks (grid and    |
      |                      |                      | DHN)                  |
      +----------------------+----------------------+-----------------------+
      | :math:`ev_{b         | [GWh]                | Battery size per V2G  |
      | att,size}(v2g)`      |                      | car technology        |
      +----------------------+----------------------+-----------------------+
      | :math:`c_            | [M€\                 | Cost to reinforce     |
      | {grid,extra}`        | :math:`_{2015}`/GW]  | the grid per GW of    |
      |                      |                      | intermittent          |
      |                      |                      | renewable             |
      +----------------------+----------------------+-----------------------+
      | :math:`elec_{        | [GW]                 | Maximum net transfer  |
      | import,max}`         |                      | capacity              |
      +----------------------+----------------------+-----------------------+
      | :math:`{solar}       | [km\ :math:`^2`]     | Available area for    |
      | _{area, rooftop}     |                      | solar panels          |
      | (reg)`               |                      | on rooftop            |
      |                      |                      | in each region        |
      +----------------------+----------------------+-----------------------+
      | :math:`{solar}       | [km\ :math:`^2`]     | Available area for    |
      | _{area, ground}(reg)`|                      | solar panels          |
      |                      |                      | on the ground         |
      |                      |                      | in each region        |
      +----------------------+----------------------+-----------------------+
      | :math:`{solar}       | [km\ :math:`^2`]     | Available area for    |
      | _{area, ground, csp} |                      | concentrated solar    |
      | (reg)`               |                      | power (CSP)           |
      |                      |                      | in each region        |
      +----------------------+----------------------+-----------------------+
      | :math:`{power}       | [GW/km\ :math:`^2`]  | Peak power density    |
      | \_density_{pv}`      |                      | of PV                 |
      +----------------------+----------------------+-----------------------+
      | :math:`{power}       | [GW :math:`_{th}`    | Peak power density    |
      | \_density_{          | /km\ :math:`^2`]     | of solar thermal      |
      | solar,thermal}`      |                      |                       |
      +----------------------+----------------------+-----------------------+
      | :math:`{power}       | [GW :math:`_{th}`    | Peak power density    |
      | \_density_{          | /km\ :math:`^2`]     | of solar parabolic    |
      | pt}`                 |                      | trough (pt)           |
      |                      |                      | power plants          |
      +----------------------+----------------------+-----------------------+
      | :math:`{power}       | [GW :math:`_{th}`    | Peak power density    |
      | \_density_{          | /km\ :math:`^2`]     | of solar tower (st)   |
      | st}`                 |                      | power plants          |
      |                      |                      |                       |
      +----------------------+----------------------+-----------------------+
      | :math:`sm_{max}`     | [-]                  | Maximum solar multiple|
      |                      |                      | for CSP plants        |
      |                      |                      |                       |
      +----------------------+----------------------+-----------------------+
      | :math:`exch_{loss}   | [-]                  | Exchanges losses      |
      | (er)`                |                      |                       |
      |                      |                      |                       |
      +----------------------+----------------------+-----------------------+
      | :math:`tc_{min},     | [GW]                 | Min./max. transfer    |
      | tc_{max}(reg, reg,   |                      | capacity for each     |
      | ner, nt(ner))`       |                      | network type of each  |
      |                      |                      | network exchange      |
      |                      |                      | resource              |
      +----------------------+----------------------+-----------------------+
      | :math:`ch4toh2`      | [-]                  | Diminution of transfer|
      |                      |                      | capacity (ratio)      |
      |                      |                      | when retrofitting     |
      |                      |                      | methane pipelines     |
      |                      |                      | to hydrogen pipelines |
      +----------------------+----------------------+-----------------------+
      | :math:`lhv(fer)`     | [-]                  | Energy density        |
      |                      |                      | of freight exchanged  |
      |                      |                      | resources             |
      +----------------------+----------------------+-----------------------+
      | :math:`dist(reg_1,   | [-]                  | Typical distance      |
      | reg_2)`              |                      | between two regions,  |
      |                      |                      | set to 0 for          |
      |                      |                      | non-neighbouring      |
      |                      |                      | regions               |
      +----------------------+----------------------+-----------------------+
      
.. [b]
   Instead of [GWh], we have [Mpkm] (millions of passenger-km) for passenger mobility and aviation,
   [Mtkm] (millions of ton-km) for freight mobility and shipping end-uses.

.. [c]
   Instead of [GW], we have [GWh] if :math:`{{tech}} \in {{STO}}`.

.. [d]
   Instead of [GW], we have [Mpkm/h] for passenger mobility and aviation end-use technologies,
   and [Mtkm/h] for freight mobility and shipping end-use technologies.


.. container::

   .. table:: Independent variables. All variables are continuous and non-negative, unless otherwise indicated.
      :name: tab:variablesIndependent
   
      +---------------------------+------------+---------------------------+
      | Variable                  | Units      | Description               |
      +===========================+============+===========================+
      | :math:`\textbf{%}_{       | [-]        | Ratio :math:`[0;1]`       |
      | \textbf{Public}}(reg)`    |            | public mobility over      |
      |                           |            | total passenger mobility  |
      +---------------------------+------------+---------------------------+
      | :math:`\textbf{%}_{       | [-]        | Ratio :math:`[0;1]`       |
      | \textbf{Av,Short}}(reg)`  |            | short-haul aviation over  |
      |                           |            | total passenger mobility  |
      +---------------------------+------------+---------------------------+
      | :math:`\textbf{%}_{       | [-]        | Ratio :math:`[0;1]` rail  |
      | \textbf{Fr,Rail}}(reg)`   |            | transport over total      |
      |                           |            | freight transport         |
      +---------------------------+------------+---------------------------+
      | :math:`\textbf{%}_{       | [-]        | Ratio :math:`[0;1]` boat  |
      | \textbf{Fr,Boat}}(reg)`   |            | transport over total      |
      |                           |            | freight transport         |
      +---------------------------+------------+---------------------------+
      | :math:`\textbf{%}_{       | [-]        | Ratio :math:`[0;1]` road  |
      | \textbf{Fr,Road}}(reg)`   |            | transport over total      |
      |                           |            | freight transport         |
      +---------------------------+------------+---------------------------+
      | :math:`\textbf{%}_{       | [-]        | Ratio :math:`[0;1]`       |
      | \textbf{Dhn}}(reg)`       |            | centralized over total    |
      |                           |            | low-temperature heat      |
      +---------------------------+------------+---------------------------+
      | :math:`\textbf{F}         | [GW] [e]_  | Installed capacity with   |
      | (reg, tech)`              |            | respect to main output    |
      +---------------------------+------------+---------------------------+
      | :math:`\textbf{F}_        | [GW] [e]_  | Operation in each period  |
      | {\textbf{t}}(reg, tech    |            |                           |
      | , h, td)`                 |            |                           |
      +---------------------------+------------+---------------------------+
      | :math:`\textbf{R}_        | [GW]       | Use of local resources    |
      | {\textbf{t,local}}(reg,   |            |                           |
      | res, h, td)`              |            |                           |
      +---------------------------+------------+---------------------------+
      | :math:`\textbf{R}_        | [GW]       | Use of resources imported |
      | {\textbf{t,ext}}(reg,     |            | from the exterior         |
      | res, h, td)`              |            |                           |
      +---------------------------+------------+---------------------------+
      | :math:`\textbf{Sto}_{     | [GW]       | Input to/output from      |
      | \textbf{in}},             |            | storage units             |
      | \textbf{Sto}_{            |            |                           |
      | \textbf{out}}             |            |                           |
      | (reg, sto, l, h, td)`     |            |                           |
      +---------------------------+------------+---------------------------+
      | :math:`\textbf{Tc}        | [GW]       | Installed transfer        |
      | (reg_1, reg_2, ner,       |            | capacity between two      |
      | nt(ner))`                 |            | regions for each network  |
      |                           |            | type (nt) of each network |
      |                           |            | exchange resource (ner)   | 
      +---------------------------+------------+---------------------------+
      | :math:`\textbf{Exch}_{    | [GW]       | Import/export of exchanged|
      | \textbf{imp}},            |            | resources to/from region 1|
      | \textbf{Exch}_{           |            | from/to region 2          |
      | \textbf{exp}}             |            |                           |
      | (reg_1, reg_2, er, h, td)`|            |                           |
      +---------------------------+------------+---------------------------+
      | :math:`\textbf{P}_{       | [GW]       | Constant load of nuclear  |
      | \textbf{Nuclear}}(reg)`   |            |                           |
      +---------------------------+------------+---------------------------+
      | :math:`\textbf{%}_{       | [-]        | Constant share of         |
      | \textbf{PassMob}}(reg,    |            | passenger mobility        |
      | TECH\_OF\_EUC(PassMob))`  |            |                           |
      +---------------------------+------------+---------------------------+
      | :math:`\textbf{%}_{       | [-]        | Constant share of         |
      | \textbf{FreightMob}}      |            | freight mobility          |
      | (reg, TECH\_OF\_EUC       |            |                           |
      | (FreightMob))`            |            |                           |
      +---------------------------+------------+---------------------------+
      | :math:`\textbf{%}_{       | [-]        | Constant share of         |
      | \textbf{Shipping}}        |            | shipping                  |
      | (reg, TECH\_OF\_EUC       |            |                           |
      | (Shipping))`              |            |                           |
      +---------------------------+------------+---------------------------+
      | :math:`\textbf{%}_{       | [-]        | Constant share of low     |
      | \textbf{HeatLowTDEC}}     |            | temperature heat          |
      | (reg, TECH\_OF\_EUT       |            | decentralised supplied    |
      | (HeatLowTDec)\setminus    |            | by a technology plus its  |
      | {Dec_{Solar}})`           |            | associated thermal solar  |
      |                           |            | and storage               |
      +---------------------------+------------+---------------------------+
      | :math:`\textbf{F}_{       | [-]        | Solar thermal installed   |
      | \textbf{sol}}             |            | capacity associated to a  |
      | (reg,TECH\_OF\_EUT        |            | decentralised heating     |
      | (HeatLowTDec)\setminus    |            | technology                |
      | {Dec_{Solar}})`           |            |                           |
      +---------------------------+------------+---------------------------+
      | :math:`\textbf{F}_{       | [-]        | Solar thermal operation   |
      | \textbf{t}_{\textbf{sol}}}|            | in each period            |
      | (reg, TECH\_OF\_EUT       |            |                           |
      | (HeatLowTDec)\setminus    |            |                           |
      | {Dec_{Solar}})`           |            |                           |
      +---------------------------+------------+---------------------------+

.. [e]
   [Mpkm] (millions of passenger-km) for passenger mobility and aviation,
   [Mtkm] (millions of ton-km) for freight mobility and shipping end-uses,
   [GWh] if :math:`tech \in STO`.


.. container::

   .. table:: Dependent variable. All variables are continuous and non-negative, unless otherwise indicated.
      :name: tab:variablesDependent

      +----------------------+----------------------+----------------------+
      | **Variable**         | **Units**            | **Description**      |
      +======================+======================+======================+
      | :math:`\textbf{      | [GW] [f]_            | End-uses demand. Set |
      | EndUses}(reg,l,h,td)`|                      | to 0 if              |
      |                      |                      | :math:`l \notin`     |
      |                      |                      | *EUT*                |
      +----------------------+----------------------+----------------------+
      | :math:`\textbf{C}_   | [M€\ :sub:`2015`/y]  | Total annual cost of |
      | {\textbf{tot}}(reg)` |                      | the energy system    |
      +----------------------+----------------------+----------------------+
      | :math:`\textbf{C}_   | [M€\ :sub:`2015`]    | Technology total     |
      | {\textbf{inv}}(reg,  |                      | investment cost      |
      | tech)`               |                      |                      |
      +----------------------+----------------------+----------------------+
      | :math:`\textbf{C}_   | [M€\ :sub:`2015`/y]  | Technology yearly    |
      | {\textbf{maint}}(reg,|                      | maintenance cost     |
      | tech)`               |                      |                      |
      +----------------------+----------------------+----------------------+
      | :math:`\textbf{C}_   | [M€\ :sub:`2015`/y]  | Total cost of        |
      | {\textbf{op}}(reg,   |                      | resources            |
      | res)`                |                      |                      |
      +----------------------+----------------------+----------------------+
      | :math:`\textbf{GWP}_ | [ktCO\               | Total yearly GHG     |
      | {\textbf{tot}}(reg)` | :math:`_2`-eq./y]    | emissions of the     |
      |                      |                      | energy system        |
      +----------------------+----------------------+----------------------+
      | :math:`\textbf{GWP}_ | [k\                  | Technology           |
      | {\textbf{constr}}(reg| tCO\ :math:`_2`-eq.] | construction GHG     |
      | , tech)`             |                      | emissions            |
      |                      |                      |                      |
      +----------------------+----------------------+----------------------+
      | :math:`\textbf{GWP}_ | [ktC\                | Total GHG emissions  |
      | {\textbf{op}}(reg,   | O\ :math:`_2`-eq./y] | of resources         |
      | res)`                |                      |                      |
      +----------------------+----------------------+----------------------+
      | :math:`\textbf{CO2}_ | [ktC\                | Total net GHG        |
      | {\textbf{net}}(reg,  | O\ :math:`_2`-eq./y] | emissions of         |
      | res)`                |                      | resources            |
      +----------------------+----------------------+----------------------+
      | :math:`\textbf{Curt} | [GW]                 | Curtailment of       |
      | (reg, tech, h ,td)`  |                      | technologies         |
      |                      |                      |                      |
      +----------------------+----------------------+----------------------+
      | :math:`\textbf{Net}_ | [GW]                 | Losses in the        |
      | {\textbf{loss}}(reg, |                      | networks (grid and   |
      | eut,h,td)`           |                      | DHN)                 |
      +----------------------+----------------------+----------------------+
      | :math:`\textbf{Sto}_ | [GWh]                | Energy stored over   |
      | {\textbf{level}}(reg,|                      | the year             |
      | sto,t)`              |                      |                      |
      +----------------------+----------------------+----------------------+
      | :math:`\textbf{R}_   | [GW]                 | Import/Export of     |
      | {\textbf{t,imp}},    |                      | resources from       |
      | \textbf{R}_          |                      | neighbouring regions |
      | {\textbf{t,exp}}     |                      |                      |
      | (reg, res, h, td)`   |                      |                      |
      +----------------------+----------------------+----------------------+
      | :math:`\textbf{Imp}_ | [GW]                 | Constant import from |
      | {\textbf{cst}}(reg,  |                      | the rest of the world|
      | res_{cst})`          |                      |                      |
      +----------------------+----------------------+----------------------+
      | :math:`\textbf{Frei  | [Mtkm]               | Additional yearly    |
      | ght}_                |                      | freight due to       |
      | {\textbf{exch,b}}    |                      | exchanges across     |
      | (reg_1,reg_2)`       |                      | each border          |
      +----------------------+----------------------+----------------------+
      | :math:`\textbf{Frei  | [Mtkm]               | Additional yearly    |
      | ght}_                |                      | freight due to       |
      | {\textbf{exch}}(reg)`|                      | exchanges for each   |
      |                      |                      | region               |
      +----------------------+----------------------+----------------------+

.. [f]
   [Mpkm] (millions of passenger-km) for passenger mobility and aviation,
   [Mtkm] (millions of ton-km) for freight mobility and shipping end-uses.

.. _ssec_lp_formulation:

Energy model formulation
~~~~~~~~~~~~~~~~~~~~~~~~

.. caution:: 
    here, update eq to ESMC and update thesis manuscript with comment FC and HJ

.. caution:: 
    update number of figs and eq

In the following, the overall linear programming formulation is proposed through :numref:`Figure %s <fig:EndUseDemand>` and equations
 :eq:`eq:obj_func` - :eq:`eq:solarAreaLimited`
the constraints are regrouped in paragraphs. It starts with the
calculation of the EUD. Then, the cost, the GWP and the objective
functions are introduced. Then, it follows with more specific
paragraphs, such as *storage* or *vehicle-to-grid* implementations.

Objective function: total annualised system cost
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The objective is the minimisation of the sum of the total annual cost of the energy system
of each region (:math:`\textbf{C}_{\textbf{tot}}`):

.. math::
    \text{min} \sum_{r \in \text{REG}} \textbf{C}_{\textbf{tot}}(r).
    :label: eq:obj_func

The total annual cost is defined as the sum of the annualized investments cost of the
technologies (:math:`\textbf{$\tau$} \textbf{C}_{\textbf{inv}}`), the operating and maintenance costs of the technologies (:math:`\textbf{C}_{\textbf{maint}}`) and
the operating cost of the resources (:math:`\textbf{C}_{\textbf{op}}`). The three elements of cost are computed for each
region:

.. math::
    \textbf{C}_{\textbf{tot}}(r) = \sum_{j \in \text{TECH}} \Big(\textbf{$\tau$}(r,j) \textbf{C}_{\textbf{inv}}(r,j) + \textbf{C}_{\textbf{maint}} (r,j)\Big) + \sum_{i \in \text{RES}} \textbf{C}_{\textbf{op}}(r,i) 
    ~~~~~~ \forall r \in \text{REG}.\\
    :label: eq:c_tot

The investment cost (:math:`\textbf{C}_{\textbf{inv}}`) is annualised with the factor :math:`\textbf{$\tau$}`, calculated based on the discount
rate (:math:`i_{\text{rate}}`) and the technology lifetime (:math:`lifetime`), Eq. :eq:`eq:tau`. The discount rate is set by default
in EnergyScope to 1.5%. This value is low compared to other studies with typical values of
7.5 to 12% :cite:`Meinke-Hubeny2017,simoes2013jrc,EuropeanCommission2016`. This low value is chosen to represent the fact that we place ourselves
as a central public investor. Having a low value gives a lower weight to investments in the
total annualised cost and thus encourages the investment. This is further discussed in the :ref:`discount_and_interest_rates` Subsection of the Input data page.

.. math::
    \textbf{$\tau$}(r,j) =  \frac{i_{\text{rate}}(i_{\text{rate}}+1)^{lifetime(r,j)}}{(i_{\text{rate}}+1)^{lifetime(r,j)} - 1} 
    ~~~~~~ \forall r \in \text{REG}, j \in \text{TECH}.\\
    :label: eq:tau

The total investment cost (:math:` \textbf{C}_{\textbf{inv}}`) of each technology results from the multiplication of its
specific investment cost (:math:`c_{\text{inv}}`) and its installed size (:math:`\textbf{F}`), the latter defined with
respect to the main output type [3]_:

.. math::
    \textbf{C}_{\textbf{inv}}(r,j) = c_{\text{inv}}(r,j) \textbf{F}(r,j) ~~~~~~ \forall r \in \text{REG}, j \in \text{TECH}.\\
    :label: eq:c_inv

The total maintenance cost is calculated similarly:

.. math::
    \textbf{C}_{\textbf{maint}}(r,j) = c_{\text{maint}}(r,j) \textbf{F}(r,j) ~~~~~~ \forall r \in \text{REG}, j \in \text{TECH}.\\ 
    :label: eq:c_maint

The operational cost of the resources is the sum of the operational cost for local resources
and the operational cost of imported resources from the exterior of the overall system.
In this mathematical formulation, the same resource can be both produced locally and
imported from the exterior. For both, it is calculated as the sum of their use (:math:`\textbf{R}_{\textbf{t,local}}` and
:math:`\textbf{R}_{\textbf{t,ext}}`, respectively) over the different periods multiplied by the period duration (:math:`t_{op}`) and
the specific cost of the resource which is different for local and exterior sources (:math:`c_{\text{op,local}}` and :math:`c_{\text{op,ext}}`):

.. math::
    \textbf{C}_{\textbf{op}}(r,i) = \sum_{t(h,td) \in T} \Big( c_{\text{op,local}}(r,i) \textbf{R}_{\textbf{t,local}}(r,i,h,td) t_{op} (h,td) + c_{\text{op,ext}}(r,i) \textbf{R}_{\textbf{t,ext}}(r,i,h,td) t_{op} (h,td) \Big)
    :label: eq:c_op

    \forall r \in \text{REG}, i \in \text{RES}.

Note that, in Eq. :eq:`eq:c_op`, hourly quantities are summed over the entire year (8760h). As we
solve the system operation on typical days, the value at each hour of the year is obtained
through a mapping on typical days. To simplify the reading, the formulation :math:`t(h,td) \in T` is
used. However, the formulation in the code is more complex and requires two additional
:math:`\text{SETS}`: :math:`\text{HOUR_OF_PERIOD(t)}` and :math:`\text{TYPICAL_DAY_OF_PERIOD(t)}`. These :math:`\text{SETS}` link each hour
of the year with its corresponding typical day and hour in the typical day. Hence, we
have: :math:`t(h,td) \in T` , which is equivalent in the code to :math:`t \in T |h \in \text{HOUR_OF_PERIOD}(t), td \in \text{TYPICAL_DAY_OF_PERIOD}(t)`.


Emissions
^^^^^^^^^

Similarly to the cost, greenhouse gas (GHG) emissions can be computed from the instal-
lation of technologies and the use of resources. The global annual GHGs emissions are
calculated using a life cycle assessment (LCA) approach, i.e. taking into account emissions
of the technologies and resources ‘*from cradle to grave*’. For climate change, the natural
choice as an indicator is the global warming potential (GWP), expressed in ktCO2-eq./year.
In Eq. :eq:`eq:GWP_tot`, the total yearly emissions of the system (:math:`\textbf{GWP}_\textbf{tot}`)
are defined as the sum of the emissions related to the construction and end-of-life of the energy conversion technologies
(:math:`\textbf{GWP}_\textbf{constr}`), allocated to one year based on the technology lifetime (:math:`lifetime`), and the
emissions related to resources (:math:`\textbf{GWP}_\textbf{op}`):

.. math::
    \textbf{GWP}_\textbf{tot}(r)  = \sum_{j \in \text{TECH}} \frac{\textbf{GWP}_\textbf{constr} (r,j)}{lifetime(r,j)} +   \sum_{i \in \text{RES}} \textbf{GWP}_\textbf{op} (r,i)
    ~~~~~~ \forall r \in \text{REG}.
    :label: eq:GWP_tot 
    
The total emissions related to the construction of technologies are the product of the
specific emissions (:math:`gwp_{\text{constr}}`) and the installed size (:math:`\textbf{F}`):

.. math::
    \textbf{GWP}_\textbf{constr}(r,j) = gwp_{\text{constr}}(r,j) \textbf{F}(r,j) ~~~~~~ \forall r \in \text{REG}, j \in \text{TECH}
    :label: eq:GWP_constr

The total emissions of the resources are the emissions, from cradle to use, associated with
resources locally produced and imported from the exterior of the overall system (:math:`gwp_\text{op}`) 
multiplied by the period duration (:math:`t_{op}`):

.. math::
    \textbf{GWP}_\textbf{op}(r,i) = \sum_{t(h,td) \in T} \Big( gwp_\text{op,local}(r,i) \textbf{R}_\textbf{t,local}(r,i,h,td)  t_{op} (h,td) + gwp_\text{op,ext}(r,i) \textbf{R}_\textbf{t,ext}(r,i,h,td)  t_{op} (h,td) \Big)
    :label: eq:GWP_op

    \forall r \in \text{REG}, i \in \text{RES}.

GHGs emissions accounting can be conducted in different manners. The European Com-
mission and the International Energy Agency (IEA) mainly use resource-related emissions
(:math:`\textbf{CO}_\textbf{2,net}`) while neglecting indirect emissions related to the extraction of those resources
(:math:`\textbf{GWP}_\textbf{op}`) or the construction of technologies (:math:`\textbf{GWP}_\textbf{constr}`). 
To facilitate the comparison with their results, a similar implementation is proposed:

.. math::
    \textbf{CO}_\textbf{2,net}(r,i) = \sum_{t(h,td) \in T} co2_\text{net}(i) \Big(  \textbf{R}_\textbf{t,local}(r,i,h,td)  t_{op} (h,td) + \textbf{R}_\textbf{t,ext}(r,i,h,td)  t_{op} (h,td) \Big)
    :label: eq:CO2_net

    \forall r \in \text{REG}, i \in \text{RES}.


End-use demand
^^^^^^^^^^^^^^

As explained before, this model uses a end-use demand (EUD) approach to define the
demand. The hourly end-use demands :math:`\big( \textbf{EndUses} \big)` are computed based on the yearly end-use 
demands (:math:`endUsesInput`), distributed according to their time series (listed in Table :numref:`%s <tab:paramsDistributions>`).
Figure :numref:`Figure %s <fig:EndUseDemand>` graphically presents the constraints associated with the hourly end-use demands
:math:`\big( \textbf{EndUses} \big)`, e.g. the public mobility demand at time t is equal to the hourly passenger
mobility demand times the public mobility share :math:`\big( \textbf{%}_{\textbf{Public}} \big)`. This computation is made for
each region.

.. figure:: /images/model_formulation/eud_eq.png
   :alt: Hourly **EndUses** demands calculation.
   :name: fig:EndUseDemand
   :width: 18cm

   Hourly end-uses demands :math:`\big( \textbf{EndUses}(r,l,hl,td), \forall r \in \text{REG}, l \in \text{EUT}, h \in \text{H}, td \in \text{TD} \big)` 
   calculation starting from yearly demand inputs :math:`\big( endUsesInput(r,eui), \forall r \in \text{REG}, eui \in \text{EUI} \big)`.
   Two main operations occur: (i) the yearly demands are dispatched into hourly demands 
   according to their time series or uniformly if the demand input does not have a time series (left operation column); 
   (ii) the demands are dispatched into end-uses types according to the end-uses technologies that can supply them (right operation column). 
   Abbreviations: space heating
   (sh), district heating network (DHN), high value chemicals (HVC), hot water (HW), passenger
   (pass), freight (fr) and non-energy demand (NED). Adapted from :cite:`Limpens2019`.


Specific electricity end-use is distributed across the periods according to its time series 
(:math:`\%_{elec}`) and is augmented by the network losses onto the regional grid 
:math:`\big( \textbf{Net}_{\textbf{loss}}(r, \text{ELEC}, h, t d) \big)`.
Low-temperature heat demand results from the sum of the yearly demand for hot water, 
evenly shared across the year, and space heating, distributed across the periods according to :math:`\%_{sh}`. 
The percentage repartition between centralized (district heating network (DHN)) 
and decentralized heat demand is defined by the variable :math:`\textbf{%}_{\textbf{Dhn}}`. 
The demand for low-temperature heat on the DHN is augmented by the losses on this network
:math:`\big( \textbf{Net}_{\textbf{loss}}(r, \text{DHN}, h, t d) \big)`. 
The space cooling is distributed across the periods according to :math:`\%_{sc}`.
High-temperature process heat and process cooling demands are evenly distributed across
the periods. Passenger mobility and long-haul aviation demands are distributed across 
the periods according to :math:`\%_{pass}`. They are expressed in millions of passenger-kilometers
(Mpkm). The variable :math:`\textbf{%}_{\textbf{Public}}` defines the penetration of public transportation 
in the passenger mobility sector and :math:`\textbf{%}_{\textbf{Av,Short}}` the share done by short-haul aviation. 
Short- and long-haul aviation are considered in a separate way as they don’t use the same type of aircraft.
Furthermore, short-haul aviation could be replaced by private or public mobility (e.g. cars
or trains) but not long-haul aviation. Freight transportation and international shipping
demand are expressed in millions of ton-kilometers (Mtkms). Freight mobility is distributed
across the periods according to :math:`\%_{fr}` time series. 
The variables :math:`\textbf{%}_{\textbf{Rail}}`, :math:`\textbf{%}_{\textbf{Boat}}` and :math:`\textbf{%}_{\textbf{Road}}` define
the share of rail, boat and road for freight mobility, respectively. The freight due energy
exchanges also augment the freight mobility demand :math:`\big( \textbf{Freight}_{\textbf{exch}}(r)/8760 \big)` [4]_. 
The shipping and non-energy demands are distributed uniformly across the periods. The non-energy
demand is dispatched into its three main feedstocks according to their share, :math:`\%_{ned}(r,HVC)`,
:math:`\%_{ned}(r,AMMONIA)` and :math:`\%_{ned}(r,METHANOL)`. This subdivision is adapted from :cite:`Rixhon2022`.

System design and operation
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Sizing of technologies
""""""""""""""""""""""

In each region, the installed capacity of a technology (:math:`\textbf{F}`) is constrained between upper and
lower bounds (:math:`f_{max}` and :math:`f_{min}`):

.. math::
    f_{\text{min}} (r,j) \leq \textbf{F}(r,j) \leq f_{\text{max}} (r,j) ~~~~~~ \forall r \in \text{REG}, j \in \text{TECH}.
    :label: eq:fmin_fmax

This formulation allows accounting for old technologies still existing in the target year
(lower bound), but also for the maximum deployment potential of a technology. As an
example, for offshore wind turbines, :math:`f_{min}` represents the existing installed capacity (which
will still be available in the future), while :math:`f_{max}` represents the maximum potential.

Capacity factors and curtailment
""""""""""""""""""""""""""""""""

The operation of technologies at each period is determined by the decision variable :math:`\textbf{F}_\textbf{t}`. 
The capacity factor of technologies is conceptually divided into two components, 
see Eqs. :eq:`eq:cp_t` and :eq:`eq:c_p`: a capacity factor for each period (:math:`c_{p,t}`) depending on resource availability (e.g.
renewables) and a yearly capacity factor (:math:`c_p`) accounting for technology downtime and
maintenance. For a given technology, the definition of only one of these two is needed,
the other being fixed to the default value of 1. For example, intermittent renewables are
constrained by an hourly capacity factor (:math:`c_{p,t} \in [0; 1]`) while CCGTs are constrained by an
annual capacity factor (:math:`c_p`, in that case 96%). When the hourly operation is lower than its
bound set by the hourly capacity factor, it is curtailed. This curtailment (:math:`\textbf{Curt}`) only makes
sense for technologies with defined hourly capacity factors (e.g. renewables).
Eqs. :eq:`eq:cp_t` and :eq:`eq:c_p` link the installed size of a technology to its actual use in each period via the two capacity factors:

.. math::
     \textbf{F}_\textbf{t}(r,j,h,td) + \textbf{Curt}(r,j,h,td) = \textbf{F}_\textbf{t}(r,j) c_{p,t} (r,j,h,td) 
     ~~~~~~ \forall r \in \text{REG}, j \in \text{TECH}, h \in \text{H}, td \in \text{TD},
    :label: eq:cp_t

.. math::
    \sum_{t(h,td) \in T} \textbf{F}_\textbf{t}(r,j,h,td) t_{op}(h,td)  \leq   \textbf{F} (r,j) c_{p} (r,j) \sum_{t(h,td) \in T} t_{op} (h,td)
    ~~~~~~ \forall r \in \text{REG}, j \in \text{TECH}.
    :label: eq:c_p


Availability of resources
"""""""""""""""""""""""""

At each period and in each region, each resource can be produced
locally (:math:`\textbf{R}_{\textbf{t,local}}`) and/or imported from the exterior of the overall energy system (:math:`\textbf{R}_{\textbf{t,ext}}`). 
In both cases, the total use of resources is limited by a yearly availability (:math:`avail_{local}` and :math:`avail_{ext}`, respectively):



.. math::
    \sum_{t(h,td) \in T} \textbf{R}_\textbf{t,local}(r,i,h,td) t_{op}(h,td)  \leq avail_{local} (r,i) 
    ~~~~~~ \forall r \in \text{REG}, i \in \text{RES},
    :label: eq:res_avail_local

.. math::
    \sum_{t(h,td) \in T} \textbf{R}_\textbf{t,ext}(r,i,h,td) t_{op}(h,td)  \leq avail_{ext} (r,i) 
    ~~~~~~ \forall r \in \text{REG}, i \in \text{RES}.
    :label: eq:res_avail_ext


For resources such as gaseous and liquid fuels (:math:`r \in \text{RES}_{\text{cst}}`), we assume that their import is
constant (:math:`\textbf{Imp}_{\textbf{cst}}`) at each hour of each typical day:

.. math::
    \textbf{R}_\textbf{t,ext}(r,i,h,td) t_{op}(h,td)  = \textbf{Imp}_{\textbf{cst}} (r,i)
    ~~~~~~ \forall r \in \text{REG}, i \in \text{RES}_{\text{cst}}, h \in \text{H}, td \in \text{TD}.
    :label: eq:res_imp_cst

This equation simulates the fact that to import these resources, the region must
install infrastructures, and these infrastructures have a certain capacity (e.g. gasoduct,
oleoduct or a port with infrastructures to inject it into the local distribution system). We
don’t model the import infrastructure and their cost but simulate the fact that to amortize
the investment, they must be used as continuously as possible. To compensate for the
fluctuating demand of the local energy system, the model has to install storage capacity for
these resources.

Layer balance
"""""""""""""

The hourly layer balance equation generalises the energy and mass balance to any energy
commodity or service:

.. math::
    \sum_{i \in \text{RES}} f(i,l) \bigg( \textbf{R}_\textbf{t,local}(r,i,h,td) + \textbf{R}_\textbf{t,ext}(r,i,h,td)
    + \textbf{R}_\textbf{t,imp}(r,i,h,td) - \textbf{R}_\textbf{t,exp}(r,i,h,td) \bigg) 
    :label: eq:layer_balance


    + \sum_{j \in \text{TECH} \setminus \text{STO}} f(j,l) \textbf{F}_\textbf{t}(r,j,h,td)
  

    + \sum_{k \in \text{STO}} \bigg(\textbf{Sto}_\textbf{out}(r,k,l,h,td) - \textbf{Sto}_\textbf{in}(r,k,l,h,td)\bigg)  


    = \textbf{EndUses}(r,l,h,td)


     
    \forall r \in \text{REG}, l \in \text{L}, h \in \text{H}, td \in \text{TD}.
  


For energy commodities, as they can be measured in terms of energy, it is indeed an
energy balance. For energy services that are not directly measured as an energy quantity
(e.g. passenger mobility measured in Mpkm/h), it expresses the fact that when energy is
converted to produce those services, they have to be used directly. For instance, if some
methane is used in buses at some hour, the public mobility ”produced” must be consumed
by the public mobility demand at the same hour. Similarly, there is a layer for captured
carbon dioxyde (CO_{2}). This layer ensures to have a mass balance for this commodity at
each hour. If a process needs CO2 to produce a synthetic fuel, this CO2 needs to be captured
from another process with carbon capture.

The matrix :math:`f` defines, for all technologies and resources, the ratio between consumption
on input layers (negative) and production on output layers (positive). For instance, a
synthetic methanation plant consumes 1.2 GW of hydrogen and 0.2 ktCO2 to produce 1 GW
of methane and 0.295 GW of DHN heat as a co-product. Eq. :eq:`eq:layer_balance` expresses the balance
for each layer: all outputs from resources and technologies (including storage) are used
to satisfy the EUD or as inputs to other resources and technologies. Resources have four
different source terms, they can be : (i) produced locally (:math:`\textbf{R}_{\textbf{t,local}}`), (ii) imported from the
exterior of the system, i.e. the global market (:math:`\textbf{R}_{\textbf{t,ext}}`), (iii) imported from neighbouring
regions considered in the model scope (:math:`\textbf{R}_{\textbf{t,imp}}`), (iv) exported to neighbouring regions
considered in the model scope (:math:`\textbf{R}_{\textbf{t,exp}}`). Similarly, storage technologies can withdraw energy
from a layer to store it (:math:`\textbf{Sto}_{\textbf{in}}`) 
or deliver energy from its storage to the layer (:math:`\textbf{Sto}_{\textbf{out}}`).


Storage
^^^^^^^

.. caution:: 
    from here, update equations

.. math::
    \textbf{Sto}_\textbf{level} (j,t) =    \textbf{Sto}_\textbf{level} (j,t-1)\cdot\left(1 - \%_{sto_{loss}}(j) \right)  
   :label: eq:sto_level

    + t_{op} (h,td)\cdot \Big(\sum_{l \in L | \eta_{\text{sto,in} (j,l) > 0}} \textbf{Sto}_\textbf{in} 	(j,l,h,td) \eta_{\text{sto,in}} (j,l) 
    
    ~~~~~~ - \sum_{l \in L | \eta_{\text{sto,out} (j,l) > 0}} \textbf{Sto}_\textbf{out} (j,l,h,td) /  \eta_{\text{sto,out}} (j,l)\Big)
    
    \forall j \in \text{STO}, \forall t \in \text{T}| \{h,td\} \in T\_H\_TD(t)


.. math::
    \textbf{Sto}_\textbf{level} (j,t) = \textbf{F}_\textbf{t} (j,h,td) ~~~~~~ \forall j \in \text{STO DAILY},\forall t \in \text{T}| \{h,td\} \in T\_H\_TD(t)
    :label: eq:Sto_level_bound_DAILY

.. math::
    \textbf{Sto}_\textbf{level} (j,t) \leq \textbf{F} (j) ~~~~~~ \forall j \in \text{STO} \setminus \text{STO DAILY},\forall t \in \text{T}  
    :label: eq:Sto_level_bound


The storage level (:math:`\textbf{Sto}_{\textbf{level}}`) at a time step (:math:`t`) is equal
to the storage level at :math:`t-1` (accounting for the losses in
:math:`t-1`), plus the inputs to the storage, minus the output from the
storage (accounting for input/output efficiencies),
Eq. :eq:`eq:sto_level`:. The storage systems which can
only be used for short-term (daily) applications are included in the
daily storage set (STO DAILY). For these units,
Eq. :eq:`eq:Sto_level_bound_DAILY`: imposes
that the storage level be the same at the end of each typical day [5]_.
Adding this constraint drastically reduces the computational time. For
the other storage technologies, which can also be used for seasonal
storage, the capacity is bounded by
Eq. :eq:`eq:Sto_level_bound`. For these units,
the storage behaviour is thus optimized over 8760h.

.. math::
    \textbf{Sto}_\textbf{in}(j,l,h,td)\cdot \Big(\lceil  \eta_{sto,in}(j,l)\rceil -1 \Big) = 0  ~~~~~~ \forall j \in \text{STO},\forall l \in \text{L}, \forall h \in \text{H}, \forall td \in \text{TD}
    :label: eq:StoInCeil

.. math::
    \textbf{Sto}_\textbf{out}(j,l,h,td)\cdot \Big(\lceil  \eta_{sto,out}(j,l)\rceil -1 \Big) = 0  ~~~~~~ \forall j \in \text{STO},\forall l \in \text{L}, \forall h \in \text{H}, \forall td \in \text{TD}
    :label: eq:StoOutCeil

.. math::
    \Big(\textbf{Sto}_\textbf{in} (j,l,h,td)t_{sto_{in}}(\text{j}) + \textbf{Sto}_\textbf{out}(j,l,h,td)t_{sto_{out}}(\text{j})\Big) \leq \textbf{F} (j)\%_{sto_{avail}}(j)
    :label: eq:LimitChargeAndDischarge

    \forall j \in STO \setminus {V2G} , \forall l \in L, \forall h \in H, \forall td \in TD


Eqs. :eq:`eq:StoInCeil` - :eq:`eq:StoOutCeil`
force the power input and output to zero if the layer is
incompatible [6]_. As an example, a PHS will only be linked to the
electricity layer (input/output efficiencies :math:`>` 0). All other
efficiencies will be equal to 0, to impede that the PHS exchanges with
incompatible layers (e.g. mobility, heat, etc).
Eq. :eq:`eq:LimitChargeAndDischarge`
limits the power input/output of a storage technology based on its
installed capacity (**F**) and three specific characteristics. First,
storage availability (:math:`\%_{sto_{avail}}`) is defined as the ratio between
the available storage capacity and the total installed capacity (default
value is 100%). This parameter is only used to realistically represent
V2G, for which we assume that only a fraction of the fleet (i.e. 20% in
these cases) can charge/discharge at the same time. Second and third,
the charging/discharging time (:math:`t_{sto_{in}}`, :math:`t_{sto_{out}}`), which are
the time to complete a full charge/discharge from empty/full
storage [7]_. As an example, a daily thermal storage needs at least 4
hours to discharge
(:math:`t_{sto_{out}}=4`\ [h]), and
another 4 hours to charge
(:math:`t_{sto_{in}}=4`\ [h]). Eq. :eq:`eq:LimitChargeAndDischarge` applies for 
all storage except electric vehicles which are limited by another constraint Eq. :eq:`eq:LimitChargeAndDischarge_ev`, presented later.

Exchanges
^^^^^^^^^

Exchanges balance
"""""""""""""""""

Network exchanges
"""""""""""""""""

Freight exchanges
"""""""""""""""""

.. caution:: 
    complete

Local networks
^^^^^^^^^^^^^^

.. math::
    \textbf{Net}_\textbf{loss}(eut,h,td) = \Big(\sum_{i \in \text{RES} \cup \text{TECH} \setminus \text{STO} | f(i,eut) > 0} f(i,eut)\textbf{F}_\textbf{t}(i,h,td) \Big) \%_{\text{net}_{loss}} (eut) 
    :label: eq:loss

    \forall eut = \text{EUT}, \forall h \in H, \forall td \in TD

.. math::
    \textbf{F} (Grid) = 1 + \frac{c_{grid,extra}}{c_{inv}(Grid)} 
    \Big(
    \textbf{F}(Wind_{onshore}) + \textbf{F}(Wind_{offshore}) + \textbf{F}(PV)
    :label: eq:mult_grid

    -\big( 
    f_{min}(Wind_{onshore}) + f_{min}(Wind_{offshore}) + f_{min}(PV)
    \big)
    \Big)

.. math::
    \textbf{F} (DHN) = \sum_{j \in \text{TECH} \setminus {STO} | f(j,\text{HeatLowTDHN}) >0} f(j,\text{HeatLowTDHN}) \cdot \textbf{F} (j) 
    :label: eq:DHNCost

Eq. :eq:`eq:loss` calculates network losses as a share
(:math:`%_{net_{loss}}`) of the total energy transferred through the network. As
an example, losses in the electricity grid are estimated to be 4.5\% of
the energy transferred in 2015 [8]_.
Eqs. :eq:`eq:mult_grid` - :eq:`eq:DHNCost`
define the extra investment for networks. Integration of intermittent RE
implies additional investment costs for the electricity grid
(:math:`c_{grid,ewtra}`). As an example, the reinforcement of the electricity
grid is estimated to be 358 millions €\ :sub:`2015` per Gigawatt of
intermittent renewable capacity installed (see 
`Data for the grid <#ssec:app1_grid:>`__ for details).
Eq. :eq:`eq:DHNCost` links the size of DHN to the total
size of the installed centralized energy conversion technologies.

Mobility shares
^^^^^^^^^^^^^^^

.. caution:: 
    add eq


Vehicle-to-grid
^^^^^^^^^^^^^^^

.. figure:: /images/model_formulation/v2gAndBatteries.png
   :alt: Illustrative example of a V2G implementation.
   :name: fig:V2GAndBatteries
   :width: 7cm

   Illustrative example of a V2G implementation. The battery can
   interact with the electricity layer. 
   The size of the battery is directly related to the number of cars (see Eq. :eq:`eq:SizeOfBEV`). 
   The V2G takes the electricity from the battery to provide a constant share (:math:`\textbf{%}_{\textbf{PassMob}}`) of the
   passenger mobility layer (*Mob. Pass.*). Thus, it imposes the amount of electricity that electric car must deserve (see Eq. :eq:`eq:BtoBEV`).
   The remaining capacity of battery available can be used to provide V2G services (see :eq:`eq:LimitChargeAndDischarge_ev`). 
   

.. math::
    \textbf{F} (i) = \frac{\textbf{F} (j)}{ veh_{capa} (j)} ev_{batt,size} (j)  ~~~~~~ \forall  j \in  V2G, i \in \text{EVs_BATT OF V2G}(j)
    :label: eq:SizeOfBEV

Vehicle-to-grid dynamics are included in the model via the *V2G* set.
For each vehicle :math:`j \in V2G`, a battery :math:`i` (:math:`i`
:math:`\in` *EVs_BATT*) is associated using the set EVs_BATT_OF_V2G
(:math:`i \in \text{EVs_BATT_OF_V2G}(j)`). Each type :math:`j`
of *V2G* has a different size of battery per car
(:math:`ev_{batt,size}(j)`), e.g. the first generation battery of the
Nissan Leaf (ZE0) has a capacity of 24 kWh [10]_. The number of vehicles
of a given technology is calculated with the installed capacity (**F**)
in [km-pass/h] and its capacity per vehicles (:math:`veh_{capa}` in
[km-pass/h/veh.]). Thus, the energy that can be stored in batteries
**F**\ (:math:`i`) of *V2G*\ (:math:`j`) is the ratio of the installed capacity of
vehicle by its specific capacity per vehicles times the size of battery
per car (:math:`ev_{batt,size}(j)`), Eq. 
:eq:`eq:SizeOfBEV`. As an example, if this technology
of cars covers 10 Mpass-km/h, and the capacity per vehicle is 50.4
pass-km/car/h (which represents an average speed of 40km/h and occupancy
of 1.26 passenger per car); thus, the amount of BEV cars are 0.198
million cars. And if a BEV has a 24kWh of battery, such as the Nissan
Leaf (ZE0), thus, the equivalent battery has a capacity of 4.76 GWh.


.. math::
    \textbf{Sto}_\textbf{out} (j,Elec,h,td) \geq - f(i,Elec) \textbf{F}_\textbf{t} (i,h,td) 
    :label: eq:BtoBEV

    \forall i \in V2G , \forall j \in \text{EVs_BATT OF V2G}(j), \forall h \in H, td \in TD 




Eq. :eq:`eq:BtoBEV` forces batteries of electric vehicles
to supply, at least, the energy required by each associated electric
vehicle technology. This lower bound is not an equality; in fact,
according to the V2G concept, batteries can also be used to support the
grid. :numref:`Figure %s <fig:V2GAndBatteries>` shows through an example
with only BEVs how Eq. :eq:`eq:BtoBEV` simplifies the
implementation of V2G. In this illustration, a battery technology is
associated to a BEV. The battery can either supply the BEV needs or
sends electricity back to the grid.

.. math::
    \textbf{Sto}_\textbf{in} (j,l,h,td)t_{sto_{in}}(\text{j}) + \Big(\textbf{Sto}_\textbf{out}(j,l,h,td) + f(i,Elec) \textbf{F}_\textbf{t} (i,h,td) \Big) \cdot t_{sto_{out}}(\text{j})
    :label: eq:LimitChargeAndDischarge_ev

    \leq \Big( \textbf{F} (j) - \frac{\textbf{F} (j)}{ veh_{capa} (j)} ev_{batt,size} (j) \Big) \cdot \%_{sto_{avail}}(j)

    \forall i \in V2G , \forall j \in \text{EVs_BATT OF V2G}(j) , \forall l \in L, \forall h \in H, \forall td \in TD

Eq. :eq:`eq:LimitChargeAndDischarge_ev` limits the availability of batteries to the number of vehicle connected to the grid.
This equation is similar to the one for other type of storage (see Eq. :eq:`eq:LimitChargeAndDischarge`); 
except that a part of the batteries are not accounted, i.e. the one running (see Eq. :eq:`eq:BtoBEV`). 
Therefore, the available output is corrected by removing the electricity powering the running car (here, :math:`f(i,Elec) \leq 0`) 
and the available batteries is corrected by removing the numbers of electric cars running (:math:`\frac{\textbf{F} (j)}{ veh_{capa} (j)} ev_{batt,size} (j)`).

.. math::
    \textbf{Sto}_\textbf{level} (j,t) \geq \textbf{F}[i] soc_{ev}(i,h)
    :label: eq:EV_min_state_of_charge

    \forall i \in V2G , \forall j \in \text{EVs_BATT OF V2G}(j) , \forall t \in T| \{h,td\} \in T\_H\_TD

For each electric vehicle (:math:`ev`), a minimum state of charge is imposed for each hour of the day \big(:math:`soc_{ev}(i,h)`\big). 
As an example, we can impose that the state of charge of EV is 60% in the morning, to ensure that cars can be used to go for work. 
Eq. :eq:`eq:EV_min_state_of_charge` imposes, for each type of `V2G`, 
that the level of charge of the EV batteries is greater than the minimum state of charge times the storage capacity.

Hydro dams
^^^^^^^^^^

.. caution::
    add eq

Concentrated solar power
^^^^^^^^^^^^^^^^^^^^^^^^

.. caution::
    add eq

Solar area
^^^^^^^^^^

.. caution::
    add eq

Decentralised heat production
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


.. math::
    \textbf{F} (Dec_{Solar}) = \sum_{j \in \text{TECH OF EUT} (\text{HeatLowTDec}) \setminus \{ 'Dec_{Solar}' \}} \textbf{F}_\textbf{sol} (j)  
    :label: eq:de_strategy_dec_total_ST

.. math::
    \textbf{F}_{\textbf{t}_\textbf{sol}} (j,h,td) \leq  \textbf{F}_\textbf{sol} (j)  c_{p,t}('Dec_{Solar}',h,td)
    :label: eq:op_strategy_dec_total_ST

    \forall j \in \text{TECH OF EUT} (\text{HeatLowTDec}) \setminus \{ 'Dec_{Solar}' \}, \forall h\in H, \forall td \in TD


\endgroup  
Thermal solar is implemented as a decentralized technology. It is always
installed together with another decentralized technology, which serves
as backup to compensate for the intermittency of solar thermal. Thus, we
define the total installed capacity of solar thermal
**F**\ ('':math:`Dec_{solar}`'') as the sum of **F\ sol**\ (:math:`j`),
Eq. :eq:`eq:de_strategy_dec_total_ST`,
where :math:`\textbf{F}_{\textbf{sol}}(j)` is the solar thermal
capacity associated to the backup technology :math:`j`.
Eq. :eq:`eq:op_strategy_dec_total_ST`
links the installed size of each solar thermal capacity
:math:`\textbf{F}_{\textbf{sol}}(j)` to its actual production
::math:`\textbf{F}_{\textbf{t}_\textbf{sol}}(j,h,td))` via the
solar capacity factor (:math:`c_{p,t}('Dec_{solar}')`).

.. math::
    \textbf{F}_\textbf{t} (j,h,td) + \textbf{F}_{\textbf{t}_\textbf{sol}} (j,h,td)  
    :label: eq:heat_decen_share

    + \sum_{l \in \text{L}}\Big( \textbf{Sto}_\textbf{out} (i,l,h,td) - \textbf{Sto}_\textbf{in} (i,l,h,td) \Big)

    = \textbf{%}_\textbf{HeatDec}(\text{j}) \textbf{EndUses}(HeatLowT,h,td) 

    \forall j \in \text{TECH OF EUT} (\text{HeatLowTDec}) \setminus \{ 'Dec_{Solar}' \}, 

    i \in \text{TS OF DEC TECH}(j)  , \forall h\in H, \forall td \in TD


.. figure:: /images/model_formulation/ts_and_Fsolv2.png
   :alt: Illustrative example of a decentralised heating layer.
   :name: fig:FsolAndTSImplementation
   :width: 12cm

   Illustrative example of a decentralised heating layer with thermal
   storage, solar thermal and two conventional production technologies,
   gas boilers and electrical HP. In this case,
   Eq. :eq:`eq:heat_decen_share` applied to the
   electrical HPs becomes the equality between the two following terms:
   left term is the heat produced by: the eHPs
   (:math:`\textbf{F}_{\textbf{t}}('eHPs',h,td)`), the solar panel
   associated to the eHPs
   (:math:`\textbf{F}_{\textbf{t}_\textbf{sol}}('eHPs',h,td)`) and
   the storage associated to the eHPs; right term is the product between
   the share of decentralised heat supplied by eHPs
   (:math:`\textbf{%}_{\textbf{HeatDec}}('eHPs')`) and heat low temperature decentralised
   demand (:math:`\textbf{EndUses}(HeatLowT,h,td)`).

A thermal storage :math:`i` is defined for each decentralised heating
technology :math:`j`, to which it is related via the set *TS OF DEC TECH*,
i.e. :math:`i`\ =\ *TS OF DEC TECH(j)*. Each thermal storage :math:`i` can store
heat from its technology :math:`j` and the associated thermal solar
:math:`\textbf{F}_{\textbf{sol}}` (:math:`j`). Similarly to the passenger mobility,
Eq. :eq:`eq:heat_decen_share` makes the model
more realistic by defining the operating strategy for decentralized
heating. In fact, in the model we represent decentralized heat in an
aggregated form; however, in a real case, residential heat cannot be
aggregated. A house heated by a decentralised gas boiler and solar
thermal panels should not be able to be heated by the electrical heat
pump and thermal storage of the neighbours, and vice-versa. Hence,
Eq. :eq:`eq:heat_decen_share` imposes that the
use of each technology (:math:`\textbf{F}_{\textbf{t}}(j,h,td)`),
plus its associated thermal solar
(:math:`\textbf{F}_{\textbf{t}_\textbf{sol}}(j,h,td)`) plus
its associated storage outputs
(:math:`\textbf{Sto}_{\textbf{out}}(i,l,h,td)`) minus its associated
storage inputs (:math:`\textbf{Sto}_{\textbf{in}}(i,l,h,td)`) should
be a constant share (:math:`\textbf{%}_{\textbf{HeatDec}}(j)`) of the decentralised heat
demand :math:`(\textbf{EndUses}(HeatLowT,h,td)`). :numref:`Figure %s <fig:FsolAndTSImplementation>` shows, through an example with
two technologies (a gas boiler and a HP), how decentralised thermal
storage and thermal solar are implemented.

Peak demand
^^^^^^^^^^^

.. math::
    \textbf{F} (j) 
    \geq
    \%_{Peak_{sh}}\max_{h\in H,td\in TD}\left\{\textbf{F}_\textbf{t}(j,h,td)\right\}
    :label: eq:dec_peak

    \forall j \in \text{TECH OF  EUT} (HeatLowTDEC)   \setminus \{ 'Dec_{Solar}'\}

.. math::
    \sum_{\hspace{3cm}j \in \text{TECH OF EUT} (HeatLowTDHN), i \in \text{STO OF EUT}(HeatLowTDHN)}
    :label: eq:dhn_peak
    
    \Big( \textbf{F} (j)+
    \textbf{F} (i)/t_{sto_{out}}(i,HeatLowTDHN)  \Big)
    
    \geq
    \%_{Peak_{sh}} \max_{h\in H,td\in TD}  \big\{ \textbf{EndUses}(HeatLowTDHN,h,td) \big\}
  
Finally,
Eqs. :eq:`eq:dec_peak` - :eq:`eq:dhn_peak`
constrain the installed capacity of low temperature heat supply. Based
on the selected TDs, the ratio between the yearly peak demand and the
TDs peak demand is defined for space heating (:math:`\%_{Peak_{sh}}`).
Eq. :eq:`eq:dec_peak` imposes that the installed
capacity for decentralised technologies covers the real peak over the
year. Similarly, Eq. :eq:`eq:dhn_peak` forces the
centralised heating system to have a supply capacity (production plus
storage) higher than the peak demand. These equations force the
installed capacity to meet the peak heating demand, i.e. which
represents, somehow, the network adequacy  [11]_.


Additional Constraints
^^^^^^^^^^^^^^^^^^^^^^

.. math::
    \textbf{F}_\textbf{t} (Nuclear,h,td) = \textbf{P}_\textbf{Nuclear}  ~~~~~~ \forall h \in H, \forall td \in TD
    :label: eq:CstNuke

Nuclear power plants are assumed to have no power variation over the
year, Eq. :eq:`eq:CstNuke`. If needed, this equation can
be replicated for all other technologies for which a constant operation
over the year is desired.

.. math::
    \textbf{F}_\textbf{t} (j,h,td) = \textbf{%}_\textbf{PassMob} (j)   \sum_{l \in EUT\_of\_EUC(PassMob)} \textbf{EndUses}(l,h,td) 
    :label: eq:mob_share_fix

    \forall j \in TECH\_OF\_EUC(PassMob) , \forall h \in H, \forall td \in TD

.. math::
    \textbf{F}_\textbf{t} (j,h,td) = \textbf{%}_\textbf{FreightMob} (j)   \sum_{l \in EUT\_of\_EUC(FreightMob)} \textbf{EndUses}(l,h,td) 
    :label: eq:freight_share_fix

    \forall j \in TECH\_OF\_EUC(FreightMob) , \forall h \in H, \forall td \in TD

.. math::
    \textbf{%}_\textbf{Fr,Rail} + \textbf{%}_\textbf{Fr,Train} + \textbf{%}_\textbf{Fr,Boat} = 1
    :label: eq:freight_share_constant


Eqs. :eq:`eq:mob_share_fix` - :eq:`eq:freight_share_fix`
impose that the share of the different technologies for mobility
(:math:`\textbf{%}_{\textbf{PassMob}}`) and (:math:`\textbf{%}_{\textbf{Freight}}`) be the same at each time
step [9]_. In other words, if 20% of the mobility is supplied by train,
this share remains constant in the morning or the afternoon.
Eq. :eq:`eq:freight_share_constant`
verifies that the freight technologies supply the overall freight demand
(this constraint is related to :numref:`Figure %s <fig:EndUseDemand>`).


.. _sssec_lp_adaptation_case_study:

Adaptations for the case study
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Additional constraints are required to implement scenarios. Scenarios
require six additional constraints
(Eqs. :eq:`eq:LimitGWP` - :eq:`eq:solarAreaLimited`)
to impose a limit on the GWP emissions, the minimum share of RE primary
energy, the relative shares of technologies, such as gasoline cars in
the private mobility, the cost of energy efficiency measures, the
electricity import power capacity and the available surface area for
solar technologies.


.. math::
    \textbf{GWP}_\textbf{tot} \leq gwp_{limit}  
    :label: eq:LimitGWP

.. math::
    \sum_{j \in  \text{RES}_\text{re},t \in T| \{h,td\} \in T\_H\_TD(t)} \textbf{F}_\textbf{t}(j,h,td)  \cdot  t_{op} (h,td)   
    :label: eq:LimitRE
    
    \geq 
    re_{share} \sum_{j \in \text{RES} ,t \in T| \{h,td\} \in T\_H\_TD(t)} \textbf{F}_\textbf{t}(j,h,td) \cdot  t_{op} (h,td)
    

To force the Belgian energy system to decrease its emissions, two lever
can constraint the annual emissions:
Eq. :eq:`eq:LimitGWP` imposes a maximum yearly
emissions threshold on the GWP (:math:`gwp_{limit}`); and
Eq. :eq:`eq:LimitRE` fixes the minimum renewable primary
energy share.

.. math::
    f_{\text{min,\%}}(j) \sum_{j' \in \text{TECH OF EUT} (eut),t \in T|\{h,td\} \in T\_H\_TD(t)}    \textbf{F}_\textbf{t}(j',h,td)\cdot t_{op}(h,td)  
    :label: eq:fmin_max_perc
    
    \leq 
 	\sum_{t \in T|\{h,td\} \in T\_H\_TD(t)}  \textbf{F}_\textbf{t} (j,h,td)\cdot t_{op}(h,td) 
    
    \leq 
    f_{\text{max,\%}}(j) \sum_{j'' \in \text{TECH OF EUT} (eut),t \in T|\{h,td\} \in T\_H\_TD(t)}    \textbf{F}_\textbf{t}(j'',h,td)\cdot t_{op}(h,td) 
    
    \forall eut \in EUT, \forall j \in \text{TECH OF EUT} (eut) 


To represent the Belgian energy system in 2015,
Eq. :eq:`eq:fmin_max_perc` imposes the relative
share of a technology in its sector.
Eq. :eq:`eq:fmin_max_perc` is complementary to
Eq. :eq:`eq:fmin_fmax`, as it expresses the minimum
(:math:`f_{min,\%}`) and maximum (:math:`f_{max,\%}`) yearly output shares of each
technology for each type of EUD. In fact, for a given technology,
assigning a relative share (e.g. boilers providing at least a given
percentage of the total heat demand) is more intuitive and close to the
energy planning practice than limiting its installed size. :math:`f_{min,\%}`
and :math:`f_{max,\%}` are fixed to 0 and 1, respectively, unless otherwise
indicated.

.. math::
    \textbf{F}(Efficiency) =  \frac{1}{1+i_{rate}} 
    :label: eq:efficiency

To account for efficiency measures from today to the target year,
Eq. :eq:`eq:efficiency` imposes their cost. The EUD
is based on a scenario detailed in 
`Data for end use demand <#sec:app1_end_uses>`__ and has a lower energy demand
than the “business as usual” scenario, which has the highest energy
demand. Hence, the energy efficiency cost accounts for all the
investment required to decrease the demand from the “business as usual”
scenario and the implemented one. As the reduced demand is imposed over
the year, the required investments must be completed before this year.
Therefore, the annualisation cost has to be deducted from one year. This
mathematically implies to define the capacity of efficiency measures
deployed to :math:`1/ (1+i_{rate})` rather than 1. The investment is
already expressed in €\ :sub:`2015`.

.. math::
    \textbf{F}_{\textbf{t}}(Electricity,h,td) \leq  elec_{import,max} ~~~~~~ \forall h \in H, \forall td \in TD
    :label: eq:elecImpLimited

.. math::
    \textbf{F}_{\textbf{t}}(i,h,td) \cdot t_{op} (h,td) =  \textbf{Import}_{\textbf{constant}}(i) ~~~~~~ \forall i \in \text{RES_IMPORT_CONSTANT}, h \in H, \forall td \in TD
    :label: eq:import_resources_constant



Eq. :eq:`eq:elecImpLimited` limits the power grid
import capacity from neighbouring countries based on a net transfer
capacity (:math:`elec_{import,max}`). Eq. :eq:`eq:import_resources_constant` imposes that some resources are imported at a constant power. 
As an example, gas and hydrogen are supposed imported at a constant flow during the year. 
In addition to offering a more realistic representation, this implementation makes it possible to visualise the level of storage within the region (i.e. gas, petrol ...).

.. caution::
    Adding too many ressource to Eq. :eq:`eq:import_resources_constant` increase drastically the computational time. 
    In this implementation, only resources expensive to store have been accounted: hydrogen and gas. 
    Other resources, such as diesel or ammonia, can be stored at a cheap price with small losses.
    By limiting to two types of resources (hydrogen and gas), the computation time is below a minute.
    By adding all resources, the computation time is above 6 minutes.


.. math::
    \textbf{F}(PV)/power\_density_{pv} 
    :label: eq:solarAreaLimited

    + \big( \textbf{F}(Dec_{Solar}) + \textbf{F}(DHN_{Solar}) \big)/power\_density_{solar~thermal}  \leq solar_{area}

In this model version, the upper limit for solar based technologies is
calculated based on the available land area (*solar\ area*) and power
densities of both PV (:math:`power\_density_{pv}`) and solar thermal
(:math:`power\_density_{solar~thermal}`),
Eq. :eq:`eq:solarAreaLimited`. The equivalence
between an install capacity (in watt peaks Wp) and the land use (in
:math:`km^2`) is calculated based on the power peak density
(in [Wp/m\ :math:`^2`]). In other words, it represents the peak power of a
one square meter of solar panel. We evaluate that PV and solar thermal
have a power peak density of :math:`power\_density_{pv}` =0.2367 and
:math:`power\_density_{solar~thermal}` =0.2857 [GW/km\ :math:`^2`] [12]_. Thus,
the land use of PV is the installed power (:math:`\textbf{F}(PV)` in [GW])
divided by the power peak density (in [GW/km\ :math:`^2`]). This area is
a lower bound of the real installation used. Indeed, here, the
calculated area correspond to the installed PV. However, in utility
plants, panels are oriented perpendicular to the sunlight. As a
consequence, a space is required to avoid shadow between rows of panels.
In the literature, the *ground cover ratio* is defined as the total
spatial requirements of large scale solar PV relative to the area of the
solar panels. This ratio is estimated around five
:cite:`dupont2020global`, which means that for each square
meter of PV panel installed, four additional square meters are needed.


.. [1]
    Passenger transport activity includes private mobility, public mobility and short-haul aviation. Each category can be supplied with different end-use technologies.

.. [3]
   Indeed, some technologies have several outputs, such as a CHP. Thus,
   the installed size must be defined with respect to one of these
   outputs. As an example, CHP are defined based on the thermal output
   rather than the electrical one.

.. [4]
   This variable is added to the road freight demand to keep a linear formulation. Furthermore, as rail and
   boat freight are always more efficient than road freight, their maximum capacity is already reached with the
   freight demand of the region. Therefore, adding the additional freight due to exchanges to the road freight 
   demand is equivalent to directly adding it to the whole freight mobility demand. This does not mean that the
   transportation of energy goods will always be done by truck in practice. Some of the energy goods might be
   more interesting to transport by train or boat than other goods, which will then be transported by truck.

.. [5]
   In most cases, the activation of the constraint stated in
   Eq. :eq:`eq:sto_level` will have as a consequence
   that the level of storage be the same at the beginning and at the end
   of each day — hence the use of the terminology ‘*daily storage*’.
   Note, however, that such daily storage behaviour is not always
   guaranteed by this constraint and thus, depending on the typical days
   sequence, a daily storage behaviour might need to be explicitly
   enforced.

.. [6]
   In the code, these equations are implemented with a *if-then*
   statement.

.. [7]
   In this linear formulation, storage technologies can charge and
   discharge at the same time. On the one hand, this avoids the need of
   integer variables; on the other hand, it has no physical meaning.
   However, in a cost minimization problem, the cheapest solution
   identified by the solver will always choose to either charge or
   discharge at any given :math:`t`, as long as cost and efficiencies
   are defined. Hence, we recommend to always verify numerically the
   fact that only storage inputs or outputs are activated at each
   :math:`t`, as we do in all our implementations.

.. [8]
   This is the ratio between the losses in the grid and the total annual
   electricity production in Belgium in 2015
   :cite:`Eurostat2017`.

.. [9]
   [foot:nonLinear]All equations expressed in a compact non-linear form
   in this section Eqs. :eq:`eq:mob_share_fix`, :eq:`eq:freight_share_fix`, 
   :eq:`eq:heat_decen_share` and :eq:`eq:dhn_peak` can be linearised. For these
   cases, the **EndUses** is defined with parameters and a variable
   representing a constant share over the year (e.g.  :math:`\textbf{%}_\textbf{public}`). As
   an example, **EndUses** in
   Eq. :eq:`eq:mob_share_fix` is equal to
   :math:`\textbf{EndUsesInput}(PassMb) \cdot %pass (h, td) / t_op (h, td)`.
   The term :math:`\textbf{%}_{\textbf{public}}`, is missing in the equation, but is implicitly
   implemented in :math:`\textbf{%}_{\textbf{PassMob}}`.

.. [10]
   This generation (ZE0) was marketed from 2010 to 2017 with a battery
   capacity of 24 kWh. The new generation (ZE1) accounts for an improved
   capacity and reaches 40 kWh per battery. Data from
   https://en.wikipedia.org/wiki/Nissan_Leaf, consulted on 08-02-2021

.. [11]
   The model resolution of the dispatch is not accurate enough to verify
   the adequacy. As one model cannot address all the issues, another
   approach has been preferred: couple the model to a dispatch one, and
   iterate between them. Percy and Coates
   :cite:`percy_coates_coupling_2020` demonstrated the
   feasibility of coupling a design model (ESTD) with a dispatch one
   (Dispa-SET :cite:`Quoilin2017`). Based on a feedback
   loop, they iterated on the design to verify the power grid adequacy
   and the strategic reserves. Results show that the backup capacities
   and storage needed to be slightly increased compared to the results
   of the design model alone.

.. [12]
   The calculation is based on the annual capacity factor, the
   conversion efficiency and the average yearly irradiation. As an
   example, for PV, the efficiency in 2035 is estimated at
   23% :cite:`DanishEnergyAgency2019` with an average daily
   irradiation - similar to historical values - of
   2820 Wh/m\ \ :math:`^2` in
   Belgium :cite:`IRM_Atlas_Irradiation`. The capacity
   factor of solar is around 11.4%, hence specific area for 1 kilowatt
   peak (:math:`kW_p`) is
   :math:`2820/24\cdot0.23/0.114\approx236.7`\ \ [:math:`MW_p`/km\ \ :math:`^2`]=\ \ :math:`0.2367`
   [:math:`GW_p`/km\ \ :math:`^2`].

