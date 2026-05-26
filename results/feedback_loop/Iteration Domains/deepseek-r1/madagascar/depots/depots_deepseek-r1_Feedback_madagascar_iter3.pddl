(define (domain Depot)
(:requirements :strips :typing)
(:types place locatable - object
	depot distributor - place
        truck hoist surface - locatable
        pallet crate - surface)

(:predicates (available ?x - hoist) 
             (lifting ?x - hoist ?y - crate)
             (at ?x - locatable ?y - place)
             (clear ?x - surface)
             (on ?x - crate ?y - surface) 
             (in ?x - crate ?y - truck))

(:action Drive
:parameters (?x - truck ?y - place ?z - place)
:precondition (and (at ?x ?y))
:effect (and (at ?x ?z) (not (at ?x ?y))))

(:action Lift
:parameters (?x - hoist ?y - crate ?z - surface ?p - place)
:precondition (and (at ?x ?p) (at ?y ?p) (available ?x) (on ?y ?z) (clear ?y))
:effect (and (lifting ?x ?y) (clear ?z) (not (on ?y ?z)) (not (at ?y ?p)) (not (clear ?y)) (not (available ?x))))

(:action Drop
:parameters (?x - hoist ?y - crate ?z - surface ?p - place)
:precondition (and (at ?x ?p) (at ?z ?p) (clear ?z) (lifting ?x ?y))
:effect (and (on ?y ?z) (clear ?y) (at ?y ?p) (available ?x) (not (lifting ?x ?y)) (not (clear ?z))))

(:action Load
:parameters (?x - hoist ?y - crate ?z - truck ?p - place)
:precondition (and (at ?x ?p) (at ?z ?p) (lifting ?x ?y))
:effect (and (in ?y ?z) (available ?x) (not (lifting ?x ?y))))

(:action Unload
:parameters (?x - hoist ?y - crate ?z - truck ?p - place)
:precondition (and (at ?x ?p) (at ?z ?p) (available ?x) (in ?y ?z))
:effect (and (lifting ?x ?y) (not (in ?y ?z)) (not (available ?x))))
)