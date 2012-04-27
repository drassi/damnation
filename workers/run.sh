#!/bin/bash

QUEUE=* rake resque:work
