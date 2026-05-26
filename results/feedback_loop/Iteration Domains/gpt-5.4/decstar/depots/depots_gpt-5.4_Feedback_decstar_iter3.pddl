(define (domain Depot)
(:requirements :strips :typing)
(:types place locatable - object
	depot distributor - place
        truck hoist surface - locatable
        pallet crate - surface)

(:predicates (available ?x - hoist)
             (clear ?x - surface)
             (on ?x - crate ?y - surface)
             (in ?x - crate ?y - truck)
             (lifting ?x - hoist ?y - crate)
             (at ?x - locatable ?y - place))

(:action Lift
:parameters (?x - hoist ?y - crate ?z - surface ?p - place)
:precondition (and (clear ?y) (on ?y ?z) (available ?x) (at ?y ?p) (at ?x ?p))
:effect (and (not (clear ?y)) (not (on ?y ?z)) (clear ?z) (lifting ?x ?y) (not (available ?x)) (not (at ?y ?p))))

(:action Drop
:parameters (?x - hoist ?y - crate ?z - surface ?p - place)
:precondition (and (lifting ?x ?y) (clear ?z) (at ?x ?p) (at ?z ?p))
:effect (and (at ?y ?p) (clear ?y) (on ?y ?z) (not (clear ?z)) (available ?x) (not (lifting ?x ?y))))

(:action Load
:parameters (?x - hoist ?y - crate ?z - truck ?p - place)
:precondition (and (lifting ?x ?y) (at ?x ?p) (at ?z ?p))
:effect (and (in ?y ?z) (available ?x) (not (lifting ?x ?y))))

(:action Unload
:parameters (?x - hoist ?y - crate ?z - truck ?p - place)
:precondition (and (in ?y ?z) (available ?x) (at ?x ?p) (at ?z ?p))
:effect (and (not (in ?y ?z)) (lifting ?x ?y) (not (available ?x))))

(:action Drive
:parameters (?x - truck ?y - place ?z - place)
:precondition (and (at ?x ?y))
:effect (and (not (at ?x ?y)) (at ?x ?z)))

)