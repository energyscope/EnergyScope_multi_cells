.. EnergyScope_Multi-Cells_documentation documentation master file, created by
   sphinx-quickstart on Thu Sep 30 10:32:01 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.


The EnergyScope Multi-Cells model
==================================
The EnergyScope Multi-Cells (ESMC) project is an open-source multi-regional whole-energy system  model. It optimises the design and hourly operation of multiple interconnected regions over a year for a target year. It is build as an extension of the regional model `EnergyScope <https://github.com/energyscope/EnergyScope/>`_.
This documentation presents the generic multi-regional whole-energy system optimization model and its implementation on a fossil-free European energy system for 2050. However, the model is suited for any multi-regional energy system and has been applied to other case studies, see :doc:`/sections/Releases` section.


.. figure:: /images/img_esmc_eu.png
   :alt: Graphical abstract
   :name: fig:graphical_abstract
   :width: 18cm

EnergyScope is mainly developped by EPFL (Switzerland) and UCLouvain (Belgium). See :doc:`/sections/Releases` section for acknowledgment, versions and publications.

Contents
=========

.. grid::

   .. grid-item-card:: :octicon:`home` Overview
      :link: sections/Overview.html

      Start with a quick summary of what is EnergyScope Multi-Cells and what it can do.

.. grid::

    .. grid-item-card:: :octicon:`book` Model formulation
        :link: sections/model_formulation.html

        Describes the mathematical formulation behind the EnergyScope Multi-Cells model.

    .. grid-item-card:: :octicon:`database` Input data
        :link: sections/Input data.html

        Describes the input data for the implementation on a fossil-free European energy system for 2050.

.. grid::

   .. grid-item-card:: :octicon:`rocket` Getting started
        :link: sections/Getting started.html

        Check out how to install and run ESMC on your machine.

   .. grid-item-card:: :octicon:`code-review` How to contribute
        :link: sections/6_Examples.html

        You want to contribute? Here are the guidelines.

.. grid::

   .. grid-item-card:: :octicon:`git-branch` Releases
        :link: sections/Releases.html

        Find here the code versions, the license, how to cite and the list of the related works.

.. toctree::
   :maxdepth: 1
   :hidden:

   sections/Overview
   sections/model_formulation
   sections/Input data
   sections/Getting started
   sections/How to contribute
   sections/Releases
   sections/Bibliography

Downloading EnergyScope
=======================


EnergyScope Multi-Cells is an open-source and collaborative project. The full code, input data and post-processing scripts can be accessed on the `github repository <https://github.com/energyscope/EnergyScope_multi_cells>`_ and cloned using the command:

        .. code-block:: bash

            git clone https://github.com/energyscope/EnergyScope_multi_cells.git

Main contributors
=================

For the EnergyScope Multi-cells model:

* Paolo **Thiran**: paolo.thiran@gmail.com
* Aurélia **Hernandez**

For the regional model EnergyScope:

* Gauthier **Limpens** : gauthierLimpens@gmail.com
* Stefano **Moret** (`website <https://www.stefanomoret.com/>`_): moret.stefano@gmail.com

There are many other developers making this model a community!
You will meet them (and their work) in :doc:`/sections/Releases` section.


