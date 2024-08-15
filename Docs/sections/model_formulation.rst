.. _ch_esmc:

Model formulation
=================

.. role:: raw-latex(raw)
   :format: latex
..




Overview
--------

The modelling with EnergyScope Multi-Cells is done in two steps; see :numref:`Figure %s <fig:model_overview_blank>`. First, a generic energy systm optimisation model is developed such
that it can be used with any multi-regional whole-energy system (middle block in :numref:`Figure %s <fig:model_overview_blank>`). This part is described in this Section. Then, the energy background of the specific case study is modelled (left block in :numref:`Figure %s <fig:model_overview_blank>`). In this documentation, the modelling of a fossil-free European energy system is described in the Section :doc:`/sections/input_data`. Other implementations are possible. For instance, the model has
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
the Section :doc:`/sections/input_data`).


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
four EUTs: passenger mobility [1]_, long-haul aviation, freight and shipping. Non-energy demand is,
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

In the following, the overall linear programming formulation is proposed through :numref:`Figure %s <fig:EndUseDemand>` and equations
 :eq:`eq:obj_func` - :eq:`eq:elecImpLimited`. The constraints are regrouped in paragraphs.


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

The total investment cost (:math:`\textbf{C}_{\textbf{inv}}`) of each technology results from the multiplication of its
specific investment cost (:math:`c_{\text{inv}}`) and its installed size (:math:`\textbf{F}`), the latter defined with
respect to the main output type [2]_:

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
exchanges also augment the freight mobility demand :math:`\big( \textbf{Freight}_{\textbf{exch}}(r)/8760 \big)` [3]_. 
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

The storage level (:math:`\textbf{Sto}_{\textbf{level}}`) at a time step (:math:`t`) is equal
to the storage level at :math:`t-1`, minus the
self-discharge losses (:math:`%_{sto_{loss}}`), plus the inputs to the storage, minus the output from the
storage (accounting for input/output efficiencies), see Eq. :eq:`eq:sto_level`.
In the code, for the first period of the year, this equation is slightly modified to set the storage level at 
the beginning of the year according to the one at the end of the year. Hence, if :math:`t=1`, 
we set :math:`t-1` to the last period of the year (8760). 

.. math::
    \textbf{Sto}_\textbf{level} (r,j,t) =    \textbf{Sto}_\textbf{level} (r,j,t-1)\cdot\left(1 - \%_{sto_{loss}}(j) \right)  
   :label: eq:sto_level

    + t_{op} (h,td)\cdot \Big(\sum_{l \in L | \eta_{\text{sto,in} (j,l) > 0}} \textbf{Sto}_\textbf{in} 	(r,j,l,h,td) \eta_{\text{sto,in}} (j,l) 
    - \sum_{l \in L | \eta_{\text{sto,out} (j,l) > 0}} \textbf{Sto}_\textbf{out} (r,j,l,h,td) /  \eta_{\text{sto,out}} (j,l)\Big)
    
    ~~~~~~~~~~~~~~ \forall r \in \text{REG}, j \in \text{STO}, \forall t(h,td) \in \text{T}.



The storage systems which can
only be used for short-term (daily) applications are included in the
daily storage set (:math:`\text{STO_DAILY}`). For these units,
Eq. :eq:`eq:Sto_level_bound_DAILY` imposes
that the storage level be the same at the end of each typical day [4]_.
Adding this constraint drastically reduces
the computational time. Indeed, this constraint reduces the number of variables by forcing
the storage level of daily storage technologies to be defined on typical days and not over the
entire year as the other storage technologies.

.. math::
    \textbf{Sto}_\textbf{level} (r,j,t) = \textbf{F}_\textbf{t} (r,j,h,td) 
    ~~~~~~ \forall r \in \text{REG}, j \in \text{STO_DAILY}, t(h,td) \in \text{T}.
    :label: eq:Sto_level_bound_DAILY

For the other storage technologies, which can also be used for seasonal
storage, the storage level is bounded by
Eq. :eq:`eq:Sto_level_bound`. For these units,
the storage behaviour is thus optimized over 8760h.


.. math::
    \textbf{Sto}_\textbf{level} (r,j,t) \leq \textbf{F} (r,j) 
    ~~~~~~ \forall r\in \text{REG}, j \in \text{STO} \setminus \text{STO_DAILY},\forall t \in \text{T}.
    :label: eq:Sto_level_bound


Eq. :eq:`eq:LimitChargeAndDischarge`
limits the power input/output of a storage technology based on its
installed capacity (**F**) and three specific characteristics. First,
storage availability (:math:`\%_{sto_{avail}}`) is defined as the ratio between
the available storage capacity and the total installed capacity (default
value is 100%). Second and third,
the charging/discharging time (:math:`t_{sto_{in}}`, :math:`t_{sto_{out}}`), which are
the time to complete a full charge/discharge from empty/full
storage. As an example, a daily thermal storage needs at least 4
hours to discharge (:math:`t_{sto_{out}}=4`\ [h]), and
another 4 hours to charge (:math:`t_{sto_{in}}=4`\ [h]). 
These two parameters are defined in each region as for some specific storage technologies (e.g. PHS), 
the discharging and charging power depends on
the location. However, these parameters generally are intrinsic characteristics of a storage
technology and are identical in all regions. Note that, in this linear formulation, storage
technologies can charge and discharge simultaneously. On the one hand, this avoids the
need for integer variables; on the other hand, it has no physical meaning. However, in a cost
minimization problem, the cheapest solution identified by the solver will always choose to
either charge or discharge at any given time, as long as cost and efficiencies are defined.
Hence, we recommend always verifying numerically the fact that only storage inputs or
outputs are activated at each hour, as we do in all our implementations.
Eq. :eq:`eq:LimitChargeAndDischarge` applies for 
all storage except electric vehicles which are limited by another constraint Eq. :eq:`eq:LimitChargeAndDischarge_ev`, presented later.

.. math::
    \Big(\textbf{Sto}_\textbf{in} (r,j,l,h,td)t_{sto_{in}}(r,j) + \textbf{Sto}_\textbf{out}(r,j,l,h,td)t_{sto_{out}}(r,j)\Big) \leq \textbf{F} (r,j)\%_{sto_{avail}}(j)
    :label: eq:LimitChargeAndDischarge

    \forall r \in \text{REG}, j \in STO \setminus \text{EVs_BATT} , \forall l \in \text{L}, \forall h \in \text{H}, td \in \text{TD}.

Eqs. :eq:`eq:StoInCeil` - :eq:`eq:StoOutCeil`
force the power input and output to zero if the layer is
incompatible [5]_. As an example, a PHS will only be linked to the
electricity layer (input/output efficiencies :math:`>` 0). All other
efficiencies will be equal to 0, to impede that the PHS exchanges with
incompatible layers (e.g. mobility, heat, etc).

.. math::
    \textbf{Sto}_\textbf{in}(r,j,l,h,td)\cdot \Big(\lceil  \eta_{sto,in}(j,l)\rceil -1 \Big) = 0  
    ~~~~~~ \forall r \in \text{REG}, j \in \text{STO}, l \in \text{L}, h \in \text{H}, td \in \text{TD},
    :label: eq:StoInCeil

.. math::
    \textbf{Sto}_\textbf{out}(r,j,l,h,td)\cdot \Big(\lceil  \eta_{sto,out}(j,l)\rceil -1 \Big) = 0  
    ~~~~~~ \forall r \in \text{REG}, j \in \text{STO}, l \in \text{L}, h \in \text{H}, td \in \text{TD}.
    :label: eq:StoOutCeil


Exchanges
^^^^^^^^^

The exchanges are modelled into two distinct categories according to the means of transportation:
(i) exchanges through a network and (ii) exchanges through freight. The resources
in each category are defined by the sets :math:`\text{NER}` and :math:`\text{FER}`, respectively. Those two categories
share equations ensuring the energy and mass balance of exchanges (Eqs. :eq:`eq:exch_balance`-:eq:`eq:noexchanges`)
but differ in terms of losses and cost constraints. Table :numref:`%s <tab:exch_formulation>` summarizes conceptually those
constraints, which are then fully described (Eqs. :eq:`eq:capa_lim_imp`-:eq:`eq:freight_exch`). On the one side, energy
carriers exchanged through a network experience some losses during transportation. They
require a transmission infrastructure whose design is optimised between certain bounds.
These optimised transfer capacities limit the quantity that can be transported across each 
border. On the other side, energy carriers’ exchanges through freight increase the freight
demand in each region involved in the exchange. This freight demand increase implies
buying more freight vehicles. Here, the exchange is only constrained by the amount that
the exporting region can provide.

.. csv-table:: Exchanges modelling into two main categories: network exchanges and freight exchanges. They differ in the way their energetic cost, investment cost and quantity constraint are formulated.
   :header:  , Network exchanges, Freight exchanges
   :widths: 30,35,35
   :name: tab:exch_formulation

    **Energetic cost**, Network losses, Additional freight demand
    **Investment cost**, Transmission infrastructure, More freight vehicle
    **Quantity constraint**, Transfer capacity, Availability of resources
    *Examples*, "*Electricity, methane*", "*Methanol, woody biomass*"



Exchanges balance
"""""""""""""""""

Eq. :eq:`eq:exch_balance` defines the energy balance of the exchanges between two regions considering
the losses during exchanges (:math:`exch_{loss}`). As exchanges have an energy cost (i.e. losses for
network exchanges or additional demand for freight exchanges), the optimisation model
never considers exchanges in both directions between two regions simultaneously. Hence,
when one region imports a certain quantity at a certain time (:math:`\textbf{Exch}_{\textbf{imp}}`), the corresponding
region exports (:math:`\textbf{Exch}_{\textbf{exp}}`) this quantity increased by the exchanges losses:

.. math::
    \textbf{Exch}_\textbf{imp}(r_1,r_2,i,h,td)\cdot \Big( 1 +  exch_{loss}(i) \cdot dist(r_1,r_2)/1000 \Big) - \textbf{Exch}_\textbf{exp}(r_1,r_2,i,h,td)
    :label: eq:exch_balance

    = -\textbf{Exch}_\textbf{imp}(r_2,r_1,i,h,td)\cdot \Big( 1 +  exch_{loss}(i) \cdot dist(r_2,r_1)/1000 \Big) + \textbf{Exch}_\textbf{exp}(r_2,r_1,i,h,td)

    \forall r_1, r_2 \in \text{REG}, i \in \text{RES}, h \in \text{H}, td \in \text{TD}.

Eq. :eq:`eq:exch_only_neigh` ensures that exchanges occur only between adjacent regions. The distance
parameter (:math:`dist`) is set by default to 0 and is only defined for adjacent regions where direct
exchanges are considered. Nevertheless, two non-adjacent regions can exchange energy
commodities with the help of one or several other regions that link them.

.. math::
    \textbf{Exch}_\textbf{imp}(r_1,r_2,i,h,td) = \textbf{Exch}_\textbf{exp}(r_1,r_2,i,h,td) = 0
    :label: eq:exch_only_neigh

    ~~~~~~~~~~~~~~~~~~~ \forall r_1, r_2 \in \text{REG}|dist(r_1,r_2)=0, i \in \text{RES}, h \in \text{H}, td \in \text{TD}.


The exchanges of each region with its adjacent regions are regrouped into total imported (:math:`\textbf{R}_{\textbf{t,imp}}`) and 
exported (:math:`\textbf{R}_{\textbf{t,exp}}`) quantities, see Eqs. :eq:`eq:r_t_imp` and :eq:`eq:r_t_exp`. Those are then included in
the layer balance of each region, see Eq. :eq:`eq:layer_balance`.

.. math::
    \textbf{R}_{\textbf{t,imp}}(r_1,i,h,td) = \sum_{r_2 \in \text{REG}} \textbf{Exch}_\textbf{imp}(r_1,r_2,i,h,td)
    ~~~~~~~ \forall r_1 \in \text{REG}, i \in \text{RES}, h \in \text{H}, td \in \text{TD},
    :label: eq:r_t_imp

    

.. math::
    \textbf{R}_{\textbf{t,exp}}(r_1,i,h,td) = \sum_{r_2 \in \text{REG}} \textbf{Exch}_\textbf{exp}(r_1,r_2,i,h,td)
    ~~~~~~~~ \forall r_1 \in \text{REG}, i \in \text{RES}, h \in \text{H}, td \in \text{TD}.
    :label: eq:r_t_exp

Eq. :eq:`eq:noexchanges` forces to have no exchanges for resources if it does not make sense. For instance,
one region cannot directly exchange its solar or wind resources. It must first convert it into
electricity or another carrier to exchange it.

.. math::
    \textbf{R}_{\textbf{t,imp}}(r,i,h,td) = \textbf{R}_{\textbf{t,exp}}(r,i,h,td) = 0
    ~~~~~~~~ \forall r \in \text{REG}, i \in \text{NOEXCHANGES}, h \in \text{H}, td \in \text{TD}.
    :label: eq:noexchanges

Network exchanges
"""""""""""""""""

For energy carriers exchanged through a network (:math:`\text{NER}`, e.g. electricity, methane, hydrogen),
at each period, the exchanges (:math:`\textbf{Exch}_{\textbf{imp}}` and :math:`\textbf{Exch}_{\textbf{exp}}`) 
are bounded by the installed transfer capacity linking the two regions (:math:`\textbf{Tc}`) 
for all network types related to this resource (:math:`\text{NT}(i)`), see
Eqs. :eq:`eq:capa_lim_imp` and :eq:`eq:capa_lim_exp`. The network type allows us to consider different onshore and offshore
interconnections. For instance, two regions can be interconnected by a hydrogen network
made of four different network types: (i) underground pipelines retrofitted from existing
methane pipelines, (ii) new underground pipelines, (iii) subsea pipelines retrofitted from
existingmethane pipelines, (iv) new subsea pipelines. The total hydrogen transfer capacity
between the two regions equals the sumof the transfer capacity of all these network types.

.. math::
    \textbf{Exch}_{\textbf{imp}}(r_1,r_2,i,h,td) \leq \sum_{n \in \text{NT}(i)} \textbf{Tc}(r_2,r_1,i,n)
    ~~~~~~~~ \forall r_1,r_2 \in \text{REG}, i \in \text{NER}, h \in \text{H}, td \in \text{TD},
    :label: eq:capa_lim_imp

.. math::
    \textbf{Exch}_{\textbf{exp}}(r_1,r_2,i,h,td) \leq \sum_{n \in \text{NT}(i)} \textbf{Tc}(r_1,r_2,i,n)
    ~~~~~~~~ \forall r_1,r_2 \in \text{REG}, i \in \text{NER}, h \in \text{H}, td \in \text{TD}.
    :label: eq:capa_lim_exp

The model can optimise the transfer capacities (:math:`\textbf{Tc}`) between all regions and for each 
network type of each resource. For all resources exchanged through a network, these
transfer capacities are limited by the parameters defining the lower and upper bounds
(:math:`tc_{min}` and :math:`tc_{max}`), see Eq. :eq:`eq:tc_bounds`. The lower bound expresses the fact that there is an existing
network that will stay in place. The upper bound allows the expansion of this existing
network.

.. math::
    tc_{min}(r_1,r_2,i,n) \leq \textbf{Tc}(r_1,r_2,i,n) \leq tc_{max}(r_1,r_2,i,n)
    ~~~~~~~~ \forall r_1,r_2 \in \text{REG}, i \in \text{NER} \setminus Methane, n \in \text{NT}(i).
    :label: eq:tc_bounds

For the methane network, specific equations are defined to consider that the existing
network can be retrofitted to a hydrogen network, see Eqs. :eq:`eq:tc_bounds_methane_pipeline` and :eq:`eq:tc_bounds_methane_subsea`. These equations
ensure that the methane network transfer capacity and themethane capacity retrofitted
to hydrogen are within the bounds of the methane network. Hydrogen is less dense than
methane. Thus, when retrofitting a methane pipeline to a hydrogen pipeline, we lose 37%
of the transfer capacity :cite:`van_rossum_european_2022`. This is expressed by the ratio ch4toh2. There are two network
types for methane: underground pipelines and subsea pipelines. Therefore, we have two
equations:

.. math::
    tc_{min}(r_1,r_2,Methane,MethanePipeline) 
    :label: eq:tc_bounds_methane_pipeline

    \leq \textbf{Tc}(r_1,r_2,Methane,MethanePipeline) + \textbf{Tc}(r_1,r_2,H2,H2Retro)/ch4toh2 \leq 

    tc_{max}(r_1,r_2,Methane,MethanePipeline)

    ~~~~~~~~ \forall r_1,r_2 \in \text{REG}.
    

.. math::
    tc_{min}(r_1,r_2,Methane,MethaneSubsea)
    :label: eq:tc_bounds_methane_subsea

    \leq \textbf{Tc}(r_1,r_2,Methane,MethaneSubsea) + \textbf{Tc}(r_1,r_2,H2,H2SubseaRetro)/ch4toh2 \leq 

    tc_{max}(r_1,r_2,Methane,MethaneSubsea)

    ~~~~~~~~ \forall r_1,r_2 \in \text{REG}.
   

In this model, it is assumed that all network transfer capacities between regions are bidirectional:

.. math::
    \textbf{Tc}(r_1,r_2,i,n) = \textbf{Tc}(r_2,r_1,i,n)
    ~~~~~~~~ \forall r_1,r_2 \in \text{REG}, i \in \text{NER}, n \in \text{NT}(i).
    :label: eq:tc_bidir

Installed transfer capacities between two regions imply an investment into the corresponding
technology in each region. This investment is proportional to the typical distance
between the region pair. Each region of the pair pays for half of the installation:

.. math::
    \textbf{F}(r_1,n) = \sum_{r_2 \in \text{REG}} \bigg(dist(r_1,r_2) \cdot \textbf{Tc}(r_2,r_1,i,n)/2 \bigg)
    ~~~~~~~~ \forall r_1 \in \text{REG}, i \in \text{NER}, n \in \text{NT}(i).
    :label: eq:tc_inv

Freight exchanges
"""""""""""""""""

The resources that can be exchanged by freight are defined by the set :math:`\text{FER}` (i.e. ammonia,
methanol, Fischer-Tropsch (FT) fuels, woody biomass and CO2). The annual freight to
transport these resources across each border (:math:`\textbf{Freight}_{\textbf{exch,b}}`) is computed in two steps, see
Eq. :eq:`eq:freight_exch_b`. First, the energy exchanged is converted into tonnes thanks to the lower heating
value (LHV) of each resource (:math:`lhv`). Second, these tonnes are converted into ton-kilometers
with the typical distance between the region pair (:math:`dist`).

.. math::
    \textbf{Freight}_{\textbf{exch,b}}(r_1,r_2) 
    :label: eq:freight_exch_b

    = dist(r_1,r_2) \sum_{i \in \text{FER}, t(h,td) \in \text{T}} \bigg( \big(\textbf{Exch}_{\textbf{imp}}(r_1,r_2,i,h,td) + \textbf{Exch}_{\textbf{exp}}(r_1,r_2,i,h,td) \big)/lhv(i) \bigg)

    ~~~~~~~~ \forall r_1,r_2 \in \text{REG}.
    

The additional freight across each border is shared evenly between the two regions of the
pair to compute the total additional freight of each region, see Eq. :eq:`eq:freight_exch`. This additional
demand is directly added to the freight demand of each region, see :numref:`Figure %s <fig:EndUseDemand>`.

.. math::
    \textbf{Freight}_{\textbf{exch}}(r_1) = \sum_{r_2 \in \text{REG}} \textbf{Freight}_{\textbf{exch,b}}(r_1,r_2)/2
    ~~~~~~~~ \forall r_1 \in \text{REG}.
    :label: eq:freight_exch

Local networks
^^^^^^^^^^^^^^

Eq. :eq:`eq:loss` calculates network losses as a share
(:math:`\%_{net_{loss}}`) of the total energy transferred through the network of each region. As
an example, losses in the electricity grid in Belgium are estimated to be 4.7\% of
the energy transferred in 2015 [6]_.

.. math::
    \textbf{Net}_\textbf{loss}(r,eut,h,td) = \Big(\sum_{j \in \text{TECH} \setminus \text{STO} | f(j,eut) > 0} f(j,eut)\textbf{F}_\textbf{t}(r,j,h,td) 
    :label: eq:loss

    + \sum_{i \in \text{RES} | f(i,eut) > 0} f(i,eut)\textbf{R}_\textbf{t,imp}(r,i,h,td) \Big) \%_{\text{net}_{loss}} (eut) 

    \forall r \in \text{REG}, eut \in \text{EUT}, h \in \text{H}, td \in \text{TD}.

Eq. :eq:`eq:mult_grid`
defines the extra investment for the local electricity network. Integration of intermittent RE
implies additional investment costs for the electricity grid
(:math:`c_{grid,extra}`). As an example, the reinforcement of the electricity
grid is estimated to be 358 millions €\ :sub:`2015` per Gigawatt of
intermittent renewable capacity installed (see 
`Data for the grid <#ssec:app1_grid:>`__ for details).


.. math::
    \textbf{F} (r,Grid) = 1 + \frac{c_{grid,extra}}{c_{inv}(r,Grid)} 
    \Big(
    \textbf{F}(r,Wind_{onshore}) + \textbf{F}(r,Wind_{offshore}) + \textbf{F}(r,PV_{utility}) + \textbf{F}(r,PV_{rooftop})
    :label: eq:mult_grid

    -\big( 
    f_{min}(r,Wind_{onshore}) + f_{min}(r,Wind_{offshore}) + f_{min}(r,PV_{utility}) + f_{min}(r,PV_{rooftop})
    \big)
    \Big)

    ~~~~~~~ \forall r \in \text{REG}.

Eq. :eq:`eq:DHNCost` links the size of DHN to the total
size of the installed centralized energy conversion technologies:

.. math::
    \textbf{F} (r,DHN) = \sum_{j \in \text{TECH_OF_EUT}(HeatLowTDHN)} \textbf{F} (r,j) ~~~~~~~ \forall r \in \text{REG}.
    :label: eq:DHNCost


Mobility shares
^^^^^^^^^^^^^^^

The share of the different technologies for passenger mobility (:math:`j \in \text{TECH_OF_EUC}(PassMob)`)
stays constant at each time step (:math:`\textbf{%}_{\textbf{PassMob}}`):

.. math::
    \textbf{F}_\textbf{t} (r,j,h,td) = \textbf{%}_\textbf{PassMob} (r,j) \cdot \big( \%_{pass}(r,h,td) \cdot endUsesInput(PassMob) \big)   
    :label: eq:mob_share_fix

    \forall r \in \text{REG}, j \in \text{TECH_OF_EUC}(PassMob) , h \in \text{H}, td \in \text{TD}.

In other words, if 20% of the passenger mobility is supplied by train, this share remains 
constant in the morning or the afternoon. But the total amount changes according to the
passenger mobility time series (:math:`\%_{pass}`). This equation approximates the fact that, in reality,
there is an entire fleet of vehicles.

Similarly, we impose that the share of the different technologies for freight mobility 
(:math:`j \in \text{TECH_OF_EUC}(FreightMob)`) and for shipping (:math:`j \in \text{TECH_OF_EUC}(Shipping)`) stays constant
at each time step (:math:`\textbf{%}_{\textbf{FreightMob}}` and :math:`\textbf{%}_{\textbf{Shipping}}`, respectively):

.. math::
    \textbf{F}_\textbf{t} (r,j,h,td) = \textbf{%}_\textbf{FreightMob} (r,j) \cdot \big( endUsesInput(FreightMob)/8760 \big)   
    :label: eq:freight_share_fix

    \forall r \in \text{REG}, j \in \text{TECH_OF_EUC}(FreightMob) , h \in \text{H}, td \in \text{TD},

.. math::
    \textbf{F}_\textbf{t} (r,j,h,td) = \textbf{%}_\textbf{Shipping} (r,j) \cdot \big( endUsesInput(Shipping)/8760 \big)   
    :label: eq:shipping_share_fix

    \forall r \in \text{REG}, j \in \text{TECH_OF_EUC}(Shipping) , h \in \text{H}, td \in \text{TD}.

For freight mobility, we ensure that the freight technologies supply the overall freight
demand by forcing the sum of shares of rail freight (:math:`\textbf{%}_{\textbf{Fr,Rail}}`), 
boat freight (:math:`\textbf{%}_{\textbf{Fr,Boat}}`) 
and road freight (:math:`\textbf{%}_{\textbf{Fr,Road}}`) to be equal to one:

.. math::
    \textbf{%}_\textbf{Fr,Rail}(r) + \textbf{%}_\textbf{Fr,Boat}(r) + \textbf{%}_\textbf{Fr,Road}(r) = 1
    ~~~~~~ \forall r \in \text{REG}.
    :label: eq:freight_share_constant


Vehicle-to-grid
^^^^^^^^^^^^^^^

Vehicle-to-grid dynamics are included in the model via the :math:`\text{V2G}` set.
For each vehicle :math:`i \in \text{V2G}`, a battery (:math:`j \in \text{EVs_BATT}`) 
is associated using the set :math:`\text{EVs_BATT_OF_V2G}`
(:math:`j \in \text{EVs_BATT_OF_V2G}(i)`). Each type :math:`i`
of :math:`\text{V2G}` has a different size of battery per car
(:math:`ev_{batt,size}(i)`), e.g. typical plug-in hybrid electric vehicle (PHEV) 
and battery electric vehicle (BEV) have different size of batteries.
A set of equations links the electric vehicles with their batteries
both for sizing and operation, see Eqs. :eq:`eq:BtoBEV`-:eq:`eq:EV_min_state_of_charge`.

The general working principle is illustrated in :numref:`Figure %s <fig:V2GAndBatteries>`. It is an example of BEVs supplying
some passenger mobility. In this illustration, a battery technology is associated with a BEV.
The battery can either supply the BEV needs or send electricity back to the grid. It can also
be charged smartly, i.e. according to the grid flexibility needs.

.. figure:: /images/model_formulation/V2GAndBatteries.png
   :alt: Illustrative example of a V2G implementation.
   :name: fig:V2GAndBatteries
   :width: 12cm

   Illustrative example of a vehicle-to-grid (V2G) implementation. The battery (EV_battery) can
   interact with the electricity layer and the battery electric vehicle (BEV). 
   The link with the electricity layer goes in both directions as the battery can be charged or 
   discharged flexibly according to the grid needs and respecting both the availability of the 
   vehicle connected to the grid and the minimum state of charge required. The link with the 
   BEV only goes in one direction as the battery is discharged to supply these vehicles with 
   power according to the demand in the passenger mobility (Mob. Pass.) layer.


Eq. :eq:`eq:BtoBEV` forces batteries of electric vehicles to supply, at least, the energy required by each 
associated electric vehicle technology. This constraint is not an equality, as batteries can
also be used to support the grid. There is a minus sign on the right side of the equation as
the car consumes electricity, and thus, the f parameter is negative.

.. math::
    \textbf{Sto}_\textbf{out} (r,j,Elec,h,td) \geq - f(i,Elec) \textbf{F}_\textbf{t} (r,i,h,td) 
    :label: eq:BtoBEV

    \forall r \in \text{REG}, i \in \text{V2G} , j \in \text{EVs_BATT_OF_V2G}(i), h \in \text{H}, td \in \text{TD}. 

The number of vehicles of a given technology is calculated by the ratio of the installed capacity (:math:`\textbf{F}`)
in [Mkm-pass/h] with the capacity per vehicle (:math:`veh_{capa}`) in
[km-pass/h/veh.]. Thus, the energy that can be stored in batteries
is this ratio times the size of battery
per car (:math:`ev_{batt,size}(j)`), Eq. :eq:`eq:SizeOfBEV`. As an example, if this technology
of cars covers 10 Mpass-km/h, and the capacity per vehicle is 50.4
pass-km/car/h (which represents an average speed of 40km/h and occupancy
of 1.26 passenger per car), the amount of BEV cars are 0.198
million cars. Thus, if a BEV has a 50kWh battery, the equivalent battery has a
capacity of 9.92 GWh.


.. math::
    \textbf{F} (r,j) = \frac{\textbf{F} (r,i)}{ veh_{capa} (i)} ev_{batt,size} (i)  
    ~~~~~~ \forall  r \in \text{REG}, i \in  \text{V2G}, j \in \text{EVs_BATT_OF_V2G}(i).
    :label: eq:SizeOfBEV

Eq. :eq:`eq:LimitChargeAndDischarge_ev` limits the availability of batteries for charging and discharging 
to the number of vehicle connected to the grid.
This equation is similar to the one for other type of storage, see Eq. :eq:`eq:LimitChargeAndDischarge`; 
except that a part of the batteries are not accounted, i.e. the batteries of the cars on the move. 
Therefore, the available output is corrected by removing the electricity powering the running car (here, :math:`f(i,Elec) \leq 0`) 
and the available batteries are corrected by removing the numbers of electric cars on the move 
(:math:`\frac{\textbf{F}_\textbf{t} (r,i,h,td)}{ veh_{capa} (i)} ev_{batt,size} (i)`). 
Furthermore, not all the stationed cars are connected to a smart charging station. Only a
share (20%) is available for charging or discharging (:math:`\%_{sto_{avail}}(j)`).


.. math::
    \textbf{Sto}_\textbf{in} (r,j,l,h,td)t_{sto_{in}}(r,j) + \Big(\textbf{Sto}_\textbf{out}(r,j,l,h,td) + 
    f(i,Elec) \textbf{F}_\textbf{t} (r,i,h,td) \Big) \cdot t_{sto_{out}}(r,j)
    :label: eq:LimitChargeAndDischarge_ev

    \leq \Big( \textbf{F} (r,j) - \frac{\textbf{F}_\textbf{t} (r,i,h,td)}{ veh_{capa} (i)} ev_{batt,size} (i) \Big) 
    \cdot \%_{sto_{avail}}(j)

    \forall r \in \text{REG}, i \in \text{V2G} , j \in \text{EVs_BATT_OF V2G}(j) , l \in \text{L}, \forall h \in \text{H}, td \in \text{TD}.


For each EV, a minimum state of charge is imposed for each hour of the day (:math:`soc_{ev}(i,h)`). 
By default, we impose that the state of charge of the EVs fleet is 60% at 7 a.m., to ensure that cars can be used to go to work. 
Eq. :eq:`eq:EV_min_state_of_charge` imposes, for each type of `V2G`, 
that the level of charge of the EV batteries is greater than the minimum state of charge times the storage capacity.

.. math::
    \textbf{Sto}_\textbf{level} (r,j,t) \geq \textbf{F}(r,j) soc_{ev}(i,h)
    ~~~~~~     \forall r \in \text{REG}, i \in \text{V2G} , j \in \text{EVs_BATT_OF_V2G}(i) , t(h,td) \in \text{T}.
    :label: eq:EV_min_state_of_charge


Hydro dams
^^^^^^^^^^

The hydro dams are implemented as the combination of two components, see 
:numref:`Figure %s <fig:hydro_dam_modelling>`: a storage unit (the reservoir or dam storage (:math:`DamSto`)) and a power production unit
(:math:`HydroDam`). We differentiate between pumped hydro storage (PHS) and the storage unit with river inflow, :math:`DamSto`.
A PHS has a lower and upper reservoir without an inlet source; a :math:`DamSto` has an inlet source,
i.e. a river inflow, but cannot pump water from the lower reservoir.

.. figure:: /images/model_formulation/hydro_dam_modelling.jpg
   :alt:  Visual representation of hydro dam modelling.
   :name: fig:hydro_dam_modelling
   :width: 17cm

   Visual representation of hydro dam modelling. This figure is adapted from :cite:`Limpens2019`.

The technology :math:`HydroDam` accounts for all the dam hydroelectric infrastructure costs
and emissions. Eqs. :eq:`eq:storage_capa_hydro_dams`-:eq:`eq:limit_hydro_dams_output` 
regulate the reservoir (:math:`DamSto`) based on the production (:math:`HydroDam`). 
Eq. :eq:`eq:storage_capa_hydro_dams` linearly relates the reservoir size with the power plant size
(:math:`\textbf{F}(r, HydroDam)`):

.. math::
    \textbf{F} (r,DamSto) \leq f_{min}(r,DamSto) 
    :label: eq:storage_capa_hydro_dams

    + \big( f_{max}(r,DamSto) - f_{min}(r,DamSto) \big) 
    \cdot \bigg(\frac{\textbf{F}(r,HydroDam) - f_{min}(r,HydroDam)}{f_{max}(r,HydroDam) - f_{min}(r,HydroDam)} \bigg)

    ~~~~~~     \forall r \in \text{REG} \setminus \text{RWITHOUTDAM}.

Eq. :eq:`eq:impose_hydro_dams_inflow` imposes the storage input power (:math:`\textbf{Sto}_\textbf{in}`) 
to be equal to the water inflow of the
dam (:math:`\textbf{F}_\textbf{t}(r, HydroDam, h, td)`). This water inflow is constrained by the hourly capacity factor
equation, see Eq. :eq:`eq:cp_t`.

.. math::
    \textbf{Sto}_\textbf{in} (r,DamSto, Elec, h, td) = \textbf{F}_\textbf{t}(r,HydroDam,h,td) 
    ~~~~~~     \forall r \in \text{REG}, h \in \text{H}, td \in \text{TD}.
    :label: eq:impose_hydro_dams_inflow

Eq. :eq:`eq:limit_hydro_dams_output` ensures that the storage output (:math:`\textbf{Sto}_\textbf{out}`) 
is lower or equal to the installed capacity
(:math:`\textbf{F}(r, HydroDam)`). Furthermore, the dam storage is constrained by the storage equations,
see Eqs. :eq:`eq:sto_level` and :eq:`eq:Sto_level_bound`.

.. math::
    \textbf{Sto}_\textbf{out} (r,DamSto, Elec, h, td) \leq \textbf{F}(r,HydroDam) 
    ~~~~~~     \forall r \in \text{REG}, h \in \text{H}, td \in \text{TD}.
    :label: eq:limit_hydro_dams_output


Concentrated solar power
^^^^^^^^^^^^^^^^^^^^^^^^

The CSP technologies are modelled into 3 elements, see :numref:`Figure %s <fig:csp_modelling>`: collectors, storage
and power block. The solar irradiance converted into heat is given by a time series and
constrained by Eq :eq:`eq:cp_t`. This heat goes onto a specific layer where it is either stored in the
CSP heat storage or converted into electricity through the power block.

.. figure:: /images/model_formulation/csp_modelling.jpg
   :alt:  Visual representation of concentrated solar power (CSP) modelling.
   :name: fig:csp_modelling
   :width: 17cm

   Visual representation of concentrated solar power (CSP) modelling.

Two different CSP technologies are considered: solar tower (ST) and parabolic trough (PT)
Each CSP technology also has its own layer representing the heat produced and stored on
the CSP plant. Eqs. :eq:`eq:sm_limit_solar_tower` and :eq:`eq:sm_limit_parabolic_trough` 
ensure that the link between the size of the collector
field :math:`\big( \textbf{F}(r, ST_{collector})` or :math:`\textbf{F}(r, PT_{collector}) \big)` 
and the size of the power block :math:`\big( \textbf{F}(r, ST_{powerblock})` or :math:`\textbf{F}(r, PT_{powerblock}) \big)` 
are kept within a realistic range. In these equations, the size of the collector
field defined in [GW:sub:`th`] is converted into equivalent electrical power (i.e. [GW:sub:`el`]) thanks to
an efficiency of the power block :math:`\big(\frac{−1}{f(ST_{powerblock},ST_{Heat})}` or 
:math:`\frac{−1}{f(PT_{powerblock},PT_{Heat})} \big)`. There is a minus
sign as the power block consumes heat (:math:`f < 0`). The link between this equivalent electrical
power and the power block size is bounded by the maximum solar multiple (:math:`sm_{max}`).
A typical maximum solar multiple of 4 is taken :cite:`dupont2020global`.

.. math::
    -\frac{\textbf{F}(r,ST_{collector})}{f(ST_{powerblock},ST_{Heat})} \leq sm_{max} \textbf{F}(r,ST_{powerblock}) 
    ~~~~~~     \forall r \in \text{REG}.
    :label: eq:sm_limit_solar_tower

.. math::
    \frac{−\textbf{F}(r,PT_{collector})}{f(PT_{powerblock},PT_{Heat})} \leq sm_{max} \textbf{F}(r,PT_{powerblock}) 
    ~~~~~~     \forall r \in \text{REG}.
    :label: eq:sm_limit_parabolic_trough

Solar area
^^^^^^^^^^

As several solar-based technologies are competing for the same locations, the upper limit
for those is calculated based on the available land area (:math:`solar_{area}`) and power densities of
PV (:math:`power\_density_{pv}`), solar thermal (:math:`power\_density_{solar~thermal}`) and 
CSP (:math:`power\_density_{pt}` and :math:`power\_density_{st}`), see
Eqs. :eq:`eq:solar_area_rooftop_limited`-:eq:`eq:solar_area_ground_high_irr_limited`. 
The equivalence between an installed capacity (in gigawatt peaks, GWp) and the
land use (in km²) is calculated based on the peak power density (GWp/km²). In other words,
it represents the peak power of one square meter of solar technology, considering also the
spacing needed between panels.

Rooftop PV and solar thermal decentralised and centralised are competing for rooftop area
(:math:`solar_{area,rooftop}`):

.. math::
    \frac{\textbf{F}(r,PV_{rooftop})}{power\_density_{pv}} 
    + \frac{\big(\textbf{F}(r,Dec_{Solar}) + \textbf{F}(r,DHN_{Solar}) \big)}{power\_density_{solar~thermal}} 
    \leq solar_{area,rooftop} (r)
    ~~~~~~~~ \forall r \in \text{REG}.
    :label: eq:solar_area_rooftop_limited
  
The utility PV and CSP technologies compete for ground area (:math:`solar_{area,ground}`):

.. math::
    \frac{\textbf{F}(r,PV_{utility})}{power\_density_{pv}} 
    + \frac{\textbf{F}(r,PT_{collector}) }{power\_density_{pt}}
    + \frac{\textbf{F}(r,ST_{collector}) }{power\_density_{st}}
    \leq solar_{area,ground} (r)
    :label: eq:solar_area_ground_limited

    ~~~~~~~~ \forall r \in \text{REG}.


Additionally, CSP technologies can only be installed on locations with annual direct normal
irradiance (DNI) above 1800 kWh/m² and a maximum slope of 2.1° :cite:`ruiz_enspreso_2019`. The two different
CSP technologies compete for that high irradiance ground area (:math:`solar_{area,ground,high~irr}`),
which is a subset of the total solar ground area (:math:`solar_{area,ground}`):

.. math::
    \frac{\textbf{F}(r,PT_{collector}) }{power\_density_{pt}}
    + \frac{\textbf{F}(r,ST_{collector}) }{power\_density_{st}}
    \leq solar_{area,ground,high~irr} (r)
    ~~~~~~~~ \forall r \in \text{REG}.
    :label: eq:solar_area_ground_high_irr_limited

Decentralised heat production
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:numref:`Figure %s <fig:FsolAndTSImplementation>` shows, through an example with
two technologies (a methane boiler and a heat pump (HP)), how decentralised heat production, thermal
storage and thermal solar are implemented.
Each heating technology can be linked with a thermal solar panel installation and thermal
storage. Together, they must supply a constant share of the decentralised heat demand.


.. figure:: /images/model_formulation/ts_and_Fsolv2.png
   :alt: Illustrative example of a decentralised heating layer.
   :name: fig:FsolAndTSImplementation
   :width: 17cm

   Illustrative example of a decentralised heating layer in one region with thermal
   storage, solar thermal and two conventional production technologies,
   methane boilers and electrical heat pumps (HPs). In this case,
   Eq. :eq:`eq:heat_decen_share` applied to the
   electrical HPs becomes the equality between the two following terms:
   left term is the heat produced by: the eHPs
   (:math:`\textbf{F}_{\textbf{t}}(r,eHPs,h,td)`), the solar panel
   associated to the eHPs
   (:math:`\textbf{F}_{\textbf{t}_\textbf{sol}}(r,eHPs,h,td)`) and
   the storage associated to the eHPs; right term is the product between
   the share of decentralised heat supplied by eHPs
   (:math:`\textbf{%}_{\textbf{HeatDec}}(eHPs)`) and heat low temperature decentralised
   demand (:math:`\textbf{EndUses}(r,HeatLowT,h,td)`).

Thermal solar, when implemented as a decentralized technology, is always
installed together with another decentralized technology, which serves
as backup to compensate for the intermittency of solar thermal. Thus, we
define the total installed capacity of solar thermal
(:math:`\textbf{F}(r,Dec_{solar})`) as the sum of the solar thermal
capacity associated with each backup technology (:math:`\textbf{F}_\textbf{sol}(r,j)`):

.. math::
    \textbf{F} (r,Dec_{Solar}) = 
    \sum_{j \in \text{TECH_OF_EUT} (HeatLowTDec) \setminus \{ Dec_{Solar} \}} \textbf{F}_\textbf{sol} (r,j)
    ~~~~~~~~ \forall r \in \text{REG}.
    :label: eq:de_strategy_dec_total_ST

Eq. :eq:`eq:op_strategy_dec_total_ST`
links the installed size of each solar thermal capacity
:math:`\big( \textbf{F}_{\textbf{sol}}(r,j) \big)` to its actual production
:math:`\big( \textbf{F}_{\textbf{t}_\textbf{sol}}(r,j,h,td) \big)` via the
solar capacity factor (:math:`c_{p,t}(r,Dec_{solar},h,td)`).

.. math::
    \textbf{F}_{\textbf{t}_\textbf{sol}} (r,j,h,td) \leq  \textbf{F}_\textbf{sol} (r,j)  c_{p,t}(r,Dec_{Solar},h,td)
    :label: eq:op_strategy_dec_total_ST

    \forall r \in \text{REG}, j \in \text{TECH_OF_EUT}(HeatLowTDec) \setminus \{ Dec_{Solar} \}, h \in \text{H}, td \in \text{TD}.


A thermal storage :math:`i` is defined for each decentralised heating
technology :math:`j`, to which it is linked via the set :math:`\text{TS_OF_DEC_TECH}`. 
Each thermal storage :math:`i` can store
heat from its technology :math:`j` and the associated thermal solar
:math:`\textbf{F}_{\textbf{sol}}(r,j)`. Similarly to the passenger mobility,
Eq. :eq:`eq:heat_decen_share` makes the model
more realistic by defining the operating strategy for decentralized
heating. In fact, in the model we represent decentralized heat in an
aggregated form; however, in a real case, residential heat cannot be
aggregated. A house heated by a decentralised methane boiler and solar
thermal panels should not be able to be heated by the electrical heat
pump and thermal storage of the neighbours, and vice-versa. Hence,
Eq. :eq:`eq:heat_decen_share` imposes that the
use of each technology (:math:`\textbf{F}_{\textbf{t}}(r,j,h,td)`),
plus its associated thermal solar
(:math:`\textbf{F}_{\textbf{t}_\textbf{sol}}(r,j,h,td)`), plus
its associated storage outputs
(:math:`\textbf{Sto}_{\textbf{out}}(r,i,l,h,td)`), minus its associated
storage inputs (:math:`\textbf{Sto}_{\textbf{in}}(r,i,l,h,td)`) should
be a constant share (:math:`\textbf{%}_{\textbf{HeatDec}}(r,j)`) of the decentralised heat
demand :math:`(\textbf{EndUses}(r,HeatLowT,h,td)`) throughout the year. 
This documentation presents Eq. :eq:`eq:heat_decen_share` in a non-linear compressed form for clarity and conciseness. 
In the model implementation, it is
linearized by directly replacing the demand variable (:math:`\textbf{EndUses}`) with the parameters that
define it: the end-use inputs and the time series.

.. math::
    \textbf{F}_\textbf{t} (r,j,h,td) + \textbf{F}_{\textbf{t}_\textbf{sol}} (r,j,h,td)
    + \sum_{l \in \text{L}}\Big( \textbf{Sto}_\textbf{out} (r,i,l,h,td) - \textbf{Sto}_\textbf{in} (r,i,l,h,td) \Big)
    = \textbf{%}_\textbf{HeatDec}(r,j) \textbf{EndUses}(r,HeatLowT,h,td) 
    :label: eq:heat_decen_share

    \forall r \in \text{REG}, j \in \text{TECH_OF_EUT}(HeatLowTDec) \setminus \{ Dec_{Solar} \}, 

    i \in \text{TS_OF_DEC_TECH}(j), h\in \text{H}, td \in \text{TD}.


Peak demand
^^^^^^^^^^^

Eqs. :eq:`eq:dec_peak` - :eq:`eq:sc_peak`
constrain the installed capacity of low temperature heat supply and space cooling supply. Based
on the selected TDs, the ratio between the yearly peak demand and the
TDs peak demand is defined for space heating and space cooling in each region 
(:math:`\%_{Peak_{sh}}(r)` and :math:`\%_{Peak_{sc}}(r)`).
These equations force the
installed capacity to meet the peak heating demand, i.e. which
represents, somehow, the network adequacy  [7]_.

Eq. :eq:`eq:dec_peak` imposes that the installed
capacity for decentralised technologies covers the real peak over the
year. This work expresses it in a non-linear form for clarity and
conciseness. In the actual model implementation, it is linearized by dividing it into two
equations.

.. math::
    \textbf{F} (r,j) 
    \geq
    \%_{Peak_{sh}}(r) \max_{h \in \text{H}, td \in \text{TD}}\left\{\textbf{F}_\textbf{t}(r,j,h,td)\right\}
    :label: eq:dec_peak

    \forall r \in \text{REG}, j \in \text{TECH_OF_EUT}(HeatLowTDEC)  \setminus \{ Dec_{Solar} \}.

Similarly, Eq. :eq:`eq:dhn_peak` forces the
centralised heating system to have a supply capacity (production plus
storage) higher than the peak demand:

.. math::
    \sum_{i,j} \Big( \textbf{F} (r,j) +  \frac{\textbf{F} (r,i)}{t_{sto_{out}}(r,i)}  \Big)
    \geq
    \%_{Peak_{sh}}(r) \max_{h\in \text{H},td\in \text{TD}}  \big\{ \textbf{EndUses}(r,HeatLowTDHN,h,td) \big\}
    :label: eq:dhn_peak

    where j \in \text{TECH_OF_EUT}(HeatLowTDHN), i \in \text{STO_OF_EUT}(HeatLowTDHN),

    \forall r \in \text{REG}.
    

Eq. :eq:`eq:sc_peak` imposes that the installed capacity for space cooling technologies covers the real
peak over the year.

.. math::
    \textbf{F} (r,j) 
    \geq
    \%_{Peak_{sc}}(r) \max_{h \in \text{H}, td \in \text{TD}}\left\{\textbf{F}_\textbf{t}(r,j,h,td)\right\}
    :label: eq:sc_peak

    \forall r \in \text{REG}, j \in \text{TECH_OF_EUT}(SpaceCooling).



Additional Constraints
^^^^^^^^^^^^^^^^^^^^^^

Conventional nuclear power plants are assumed to have no power variation over the
year, see Eq. :eq:`eq:CstNuke`. If needed, this equation can
be replicated for all other technologies for which a constant operation
over the year is desired.


.. math::
    \textbf{F}_\textbf{t} (r,Nuclear,h,td) = \textbf{P}_\textbf{Nuclear}(r)  
    ~~~~~~ \forall r \in \text{REG}, h \in \text{H}, \forall td \in \text{TD}.
    :label: eq:CstNuke

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
already expressed in M€\ :sub:`2015`.

.. math::
    \textbf{F}(r,Efficiency) =  \frac{1}{1+i_{rate}} 
    :label: eq:efficiency

.. _sssec_lp_adaptation_case_study:

Adaptations for the case study
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Additional constraints are coded to implement scenarios. 
They are not used in all scenarios,
and scenarios can be set in other ways, 
but they facilitate setting certain typical scenario constraints.

To go into the direction of the energy transition, there are three possible levers. The first
lever, using Eq. :eq:`eq:LimitGWP`, imposes a maximum yearly emissions threshold on the overall GWP
(:math:`gwp_{limit,overall}`):

.. math::
    \sum_{r \in \text{REG}} \textbf{GWP}_\textbf{tot}(r) \leq gwp_{limit,overall}.  
    :label: eq:LimitGWP

The second lever, using Eq. :eq:`eq:LimitRE`, fixes the minimum renewable primary energy share in
each region. The third lever, using Eq. :eq:`eq:res_avail_ext`, can force regions to use less fossil resources by
reducing their availability (:math:`avail_{ext}`).

.. math::
    \sum_{j \in  \text{RES}_\text{re},t(h,td) \in \text{T}} \bigg( \textbf{R}_\textbf{t,local}(r,j,h,td)
    + \textbf{R}_\textbf{t,ext}(r,j,h,td) + \textbf{R}_\textbf{t,imp}(r,j,h,td) \bigg)  \cdot  t_{op} (h,td)   
    :label: eq:LimitRE
    
    \geq 
    re_{share}(r) \sum_{j \in  \text{RES},t(h,td) \in \text{T}} \bigg( \textbf{R}_\textbf{t,local}(r,j,h,td)
    + \textbf{R}_\textbf{t,ext}(r,j,h,td) + \textbf{R}_\textbf{t,imp}(r,j,h,td) \bigg)  \cdot  t_{op} (h,td)

    \forall r \in \text{REG}. 
    
Themodel also has the ability to represent a historical energy system of the regions studied.
This is done thanks to Eq. :eq:`eq:fmin_max_perc`, which imposes the relative technology share in its sector.
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
    f_{\text{min,%}}(r,j) \sum_{j' \in \text{TECH_OF_EUT} (eut),t(h,td) \in \text{T}} 
    \textbf{F}_\textbf{t}(r,j',h,td)\cdot t_{op}(h,td)  
    :label: eq:fmin_max_perc
    
    \leq 
 	\sum_{t(h,td) \in \text{T}}  \textbf{F}_\textbf{t} (r,j,h,td) \cdot t_{op}(h,td) 
    
    \leq 
    f_{\text{max,%}}(r,j) \sum_{j'' \in \text{TECH_OF_EUT} (eut),t(h,td) \in \text{T}}    \textbf{F}_\textbf{t}(r,j'',h,td)\cdot t_{op}(h,td) 
    
    \forall r \in \text{REG}, eut \in EUT, j \in \text{TECH_OF_EUT} (eut). 


Eq. :eq:`eq:elecImpLimited` limits the power grid import capacity from neighbouring regions that are outside
of the modelled regions, based on a net transfer capacity (:math:`elec_{import,max}`). This equation can
be used with Eq. :eq:`eq:res_avail_ext`, which defines the total quantity of electricity that can be imported.
If this quantity is 0, then no imports from outside of the modelled area are considered, and
Eq. :eq:`eq:elecImpLimited` can be neglected.

.. math::
    \textbf{R}_{\textbf{t,ext}}(r,Electricity,h,td) \leq  elec_{import,max}(r) 
    ~~~~~~ \forall r \in \text{REG}, h \in \text{H}, td \in \text{TD}.
    :label: eq:elecImpLimited

Footnotes
---------

.. [1]
    Passenger transport activity includes private mobility, public mobility and short-haul aviation. Each category can be supplied with different end-use technologies.

.. [2]
   Indeed, some technologies have several outputs, such as a CHP. Thus,
   the installed size must be defined with respect to one of these
   outputs. For example, CHP are defined based on the thermal output
   rather than the electrical one.

.. [3]
   This variable is added to the road freight demand to keep a linear formulation. Furthermore, as rail and
   boat freight are always more efficient than road freight, their maximum capacity is already reached with the
   freight demand of the region. Therefore, adding the additional freight due to exchanges to the road freight 
   demand is equivalent to directly adding it to the whole freight mobility demand. This does not mean that the
   transportation of energy goods will always be done by truck in practice. Some of the energy goods might be
   more interesting to transport by train or boat than other goods, which will then be transported by truck.

.. [4]
   In most cases, the activation of the constraint stated in
   Eq. :eq:`eq:sto_level` will have as a consequence
   that the level of storage be the same at the beginning and at the end
   of each day — hence the use of the terminology ‘*daily storage*’.
   Note, however, that such daily storage behaviour is not always
   guaranteed by this constraint and thus, depending on the typical days
   sequence, a daily storage behaviour might need to be explicitly
   enforced.

.. [5]
   In the code, these equations are implemented with a *if-then*
   statement.

.. [6]
   This is the ratio between the losses in the grid and the total annual
   electricity production in Belgium in 2015
   :cite:`Eurostat2017`.

.. [7]
   The model resolution of the dispatch is not accurate enough to verify
   the adequacy. As one model cannot address all the issues, another
   approach has been preferred: couple the model to a dispatch one, and
   iterate between them. This was tested by Pavicevic et al. :cite:`pavivcevic2022bi` 
   on the regional version of the EnergyScope model by coupling it 
   with a dispatch model (Dispa-SET :cite:`Quoilin2017`). Based on a feedback
   loop, they iterated on the design to verify the power grid adequacy
   and the strategic reserves. Results show that the backup capacities
   and storage needed to be slightly increased compared to the results
   of the design model alone.

