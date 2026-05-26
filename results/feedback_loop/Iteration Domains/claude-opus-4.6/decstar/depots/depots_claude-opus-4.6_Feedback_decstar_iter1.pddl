(define (domain Depot)
(:requirements :strips :typing)
(:types place locatable - object
	depot distributor - place
        truck hoist surface - locatable
        pallet crate - surface)

(:predicates (clear ?x - surface)
             (on ?x - crate ?y - surface)
             (in ?x - crate ?y - truck)
             (lifting ?x - hoist ?y - crate)
             (available ?x - hoist)
             (at ?x - locatable ?y - place))

(:action Drive
:parameters (?x - truck ?y - place ?z - place)
:precondition (and (at ?x ?y))
:effect (and (not (at ?x ?y)) (at ?x ?z)))

(:action Lift
:parameters (?y - crate ?z - surface ?x - hoist ?p - place)
:precondition (and (on ?y ?z) (clear ?y) (at ?y ?p) (available ?x) (at ?x ?p))
:effect (and (not (on ?y ?z)) (clear ?z) (not (clear ?y)) (not (at ?y ?p)) (lifting ?x ?y) (not (available ?x))))

(:action Drop
:parameters (?y - crate ?z - surface ?x - hoist ?p - place)
:precondition (and (clear ?z) (lifting ?x ?y) (at ?z ?p) (at ?x ?p))
:effect (and (on ?y ?z) (clear ?y) (at ?y ?p) (not (clear ?z)) (not (lifting ?x ?y)) (available ?x)))

(:action Load
:parameters (?y - crate ?z - truck ?x - hoist ?p - place)
:precondition (and (lifting ?x ?y) (at ?x ?p) (at ?z ?p))
:effect (and (in ?y ?z) (not (lifting ?x ?y)) (available ?x)))

(:action Unload
:parameters (?y - crate ?z - truck ?x - hoist ?p - place)
:precondition (and (in ?y ?z) (available ?x) (at ?x ?p) (at ?z ?p))
:effect (and (not (in ?y ?z)) (lifting ?x ?y) (not (available ?x))))

)