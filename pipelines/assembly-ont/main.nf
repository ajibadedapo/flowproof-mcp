#!/usr/bin/env nextflow

nextflow.enable.dsl = 2

params.reads = null
params.genome_size = '5m'
params.outdir = 'results'
params.assemble = false

process READ_STATS {
    publishDir "${params.outdir}", mode: 'copy'
    tag "read_stats"

    input:
    path reads

    output:
    path 'read_stats.txt', emit: stats

    script:
    """
    total=\$(( \$(zcat -f ${reads} | wc -l) / 4 ))
    bases=\$(zcat -f ${reads} | awk 'NR%4==2 { n += length(\$0) } END { print n }')
    {
      echo "input=${reads}"
      echo "reads=\${total}"
      echo "bases=\${bases}"
      echo "genome_size=${params.genome_size}"
    } > read_stats.txt
    """
}

process ASSEMBLE_FLYE {
    publishDir "${params.outdir}", mode: 'copy'
    container 'staphb/flye:2.9.3'
    tag "flye"

    input:
    path reads

    output:
    path 'assembly.fasta', emit: assembly

    script:
    """
    flye --nano-raw ${reads} --genome-size ${params.genome_size} --out-dir flye_out --threads ${task.cpus}
    cp flye_out/assembly.fasta assembly.fasta
    """
}

workflow {
    if( !params.reads ) {
        error "Provide --reads <fastq[.gz]>"
    }
    reads_ch = Channel.fromPath(params.reads, checkIfExists: true)
    READ_STATS(reads_ch)
    if( params.assemble ) {
        ASSEMBLE_FLYE(reads_ch)
    }
}
