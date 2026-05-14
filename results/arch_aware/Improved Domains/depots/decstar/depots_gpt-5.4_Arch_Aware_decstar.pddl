(define (domain Depot)
(:requirements :strips :typing)
(:types place locatable - object
	depot distributor - place
        truck hoist surface - locatable
        pallet crate - surface)

(:predicates (available ?x - hoist)
             (clear ?x - surface)
             (at ?x - locatable ?y - place)
             (lifting ?x - hoist ?y - crate)
             (on ?x - crate ?y - surface)
             (in ?x - crate ?y - truck))

(:action Drive
:parameters (?x - truck ?y - place ?z - place)
:precondition (and (at ?x ?y))
:effect (and (not (at ?x ?y)) (at ?x ?z)))

(:action Lift
:parameters (?x - hoist ?y - crate ?z - surface ?p - place)
:precondition (and (at ?y ?p) (on ?y ?z) (clear ?y) (at ?x ?p) (available ?x))
:effect (and (not (at ?y ?p)) (not (clear ?y)) (not (on ?y ?z)) (lifting ?x ?y) (not (available ?x)) (clear ?z)))

(:action Drop
:parameters (?x - hoist ?y - crate ?z - surface ?p - place)
:precondition (and (lifting ?x ?y) (at ?z ?p) (clear ?z) (at ?x ?p))
:effect (and (at ?y ?p) (clear ?y) (on ?y ?z) (available ?x) (not (lifting ?x ?y)) (not (clear ?z))))

(:action Unload
:parameters (?x - hoist ?y - crate ?z - truck ?p - place)
:precondition (and (in ?y ?z) (at ?x ?p) (at ?z ?p) (available ?x))
:effect (and (not (in ?y ?z)) (lifting ?x ?y) (not (available ?x))))

(:action Load
:parameters (?x - hoist ?y - crate ?z - truck ?p - place)
:precondition (and (lifting ?x ?y) (at ?x ?p) (at ?z ?p))
:effect (and (in ?y ?z) (not (lifting ?x ?y)) (available ?x)))

)