(define (domain Depot)
(:requirements :strips :typing)
(:types place locatable - object
	depot distributor - place
        truck hoist surface - locatable
        pallet crate - surface)

(:predicates (clear ?x - surface)
             (on ?x - crate ?y - surface)
             (in ?x - crate ?y - truck)
             (available ?x - hoist)
             (lifting ?x - hoist ?y - crate)
             (at ?x - locatable ?y - place))

(:action Drive
:parameters (?x - truck ?y - place ?z - place)
:precondition (and (at ?x ?y))
:effect (and (not (at ?x ?y)) (at ?x ?z)))

(:action Lift
:parameters (?x - hoist ?y - crate ?z - surface ?p - place)
:precondition (and (at ?y ?p) (on ?y ?z) (clear ?y) (at ?x ?p) (available ?x))
:effect (and (not (on ?y ?z)) (not (clear ?y)) (not (at ?y ?p)) (clear ?z) (lifting ?x ?y) (not (available ?x))))

(:action Drop
:parameters (?x - hoist ?y - crate ?z - surface ?p - place)
:precondition (and (lifting ?x ?y) (at ?z ?p) (clear ?z) (at ?x ?p))
:effect (and (not (lifting ?x ?y)) (available ?x) (on ?y ?z) (not (clear ?z)) (clear ?y) (at ?y ?p)))

(:action Load
:parameters (?x - hoist ?y - crate ?z - truck ?p - place)
:precondition (and (lifting ?x ?y) (at ?x ?p) (at ?z ?p))
:effect (and (not (lifting ?x ?y)) (available ?x) (in ?y ?z)))

(:action Unload
:parameters (?x - hoist ?y - crate ?z - truck ?p - place)
:precondition (and (in ?y ?z) (at ?x ?p) (at ?z ?p) (available ?x))
:effect (and (not (in ?y ?z)) (not (available ?x)) (lifting ?x ?y)))

)