def remove_redundanc(infile, outfile):
    lines_seen = set() # holds lines already seen
    outfile = open(outfile, "w")
    for line in open(infile, "r"):
        if line not in lines_seen: # not a duplicate
            # line.read().replace('[get]','')
            outfile.write(line)
            lines_seen.add(line)
            
            
def remove_get(infile, outfile):
    with open(infile, 'r') as file:
        unique_lines = set()

        for line in file:
            line = line.strip()
            if "[get]" not in line:
                unique_lines.add(line)

    with open(outfile, 'w') as file:
        for line in unique_lines:
            file.write(line + '\n')

# remove_get("url_req.txt", "uniq_req.txt")
#remove_redundanc("url_req.txt", "uniq_req.txt")
#remove_redundanc("url_form.txt", "uniq_form.txt")
remove_redundanc("edge.txt", "edge_uniq.txt")