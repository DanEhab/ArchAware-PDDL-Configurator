(define (domain Depot)
(:requirements :strips :typing)
(:types place locatable - object
	depot distributor - place
        truck hoist surface - locatable
        pallet crate - surface)

(:predicates (on ?x - crate ?y - surface) 
             (clear ?x - surface)
             (in ?x - crate ?y - truck)
             (lifting ?x - hoist ?y - crate)
             (available ?x - hoist)
             (at ?x - locatable ?y - place))
	
(:action Drop
:parameters (?x - hoist ?y - crate ?z - surface ?p - place)
:precondition (and (clear ?z) (at ?x ?p) (at ?z ?p) (lifting ?x ?y))
:effect (and (on ?y ?z) (at ?y ?p) (clear ?y) (available ?x) (not (lifting ?x ?y)) (not (clear ?z))))

(:action Drive
:parameters (?x - truck ?y - place ?z - place) 
:precondition (and (at ?x ?y))
:effect (and (at ?x ?z) (not (at ?x ?y))))

(:action Unload 
:parameters (?x - hoist ?y - crate ?z - truck ?p - place)
:precondition (and (available ?x) (at ?x ?p) (at ?z ?p) (in ?y ?z))
:effect (and (lifting ?x ?y) (not (in ?y ?z)) (not (available ?x))))

(:action Load
:parameters (?x - hoist ?y - crate ?z - truck ?p - place)
:precondition (and (at ?x ?p) (at ?z ?p) (lifting ?x ?y))
:effect (and (in ?y ?z) (available ?x) (not (lifting ?x ?y))))

(:action Lift
:parameters (?x - hoist ?y - crate ?z - surface ?p - place)
:precondition (and (at ?x ?p) (available ?x) (at ?y ?p) (on ?y ?z) (clear ?y))
:effect (and (lifting ?x ?y) (clear ?z) (not (at ?y ?p)) (not (clear ?y)) (not (available ?x)) (not (on ?y ?z))))

)