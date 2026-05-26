(define (domain Depot)
(:requirements :strips :typing)
(:types place locatable - object
	depot distributor - place
        truck hoist surface - locatable
        pallet crate - surface)

(:predicates (on ?x - crate ?y - surface) 
             (lifting ?x - hoist ?y - crate)
             (clear ?x - surface)
             (available ?x - hoist)
             (in ?x - crate ?y - truck)
             (at ?x - locatable ?y - place))
	
(:action Drop
:parameters (?x - hoist ?y - crate ?z - surface ?p - place)
:precondition (and (lifting ?x ?y) (clear ?z) (at ?z ?p) (at ?x ?p))
:effect (and (on ?y ?z) (at ?y ?p) (clear ?y) (available ?x) (not (lifting ?x ?y)) (not (clear ?z))))

(:action Unload 
:parameters (?x - hoist ?y - crate ?z - truck ?p - place)
:precondition (and (available ?x) (in ?y ?z) (at ?z ?p) (at ?x ?p))
:effect (and (lifting ?x ?y) (not (in ?y ?z)) (not (available ?x))))

(:action Lift
:parameters (?x - hoist ?y - crate ?z - surface ?p - place)
:precondition (and (on ?y ?z) (clear ?y) (available ?x) (at ?y ?p) (at ?x ?p))
:effect (and (lifting ?x ?y) (clear ?z) (not (at ?y ?p)) (not (clear ?y)) (not (available ?x)) (not (on ?y ?z))))

(:action Load
:parameters (?x - hoist ?y - crate ?z - truck ?p - place)
:precondition (and (lifting ?x ?y) (at ?z ?p) (at ?x ?p))
:effect (and (in ?y ?z) (available ?x) (not (lifting ?x ?y))))

(:action Drive
:parameters (?x - truck ?y - place ?z - place) 
:precondition (and (at ?x ?y))
:effect (and (at ?x ?z) (not (at ?x ?y))))

)