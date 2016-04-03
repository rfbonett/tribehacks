from nltk.tag import pos_tag
from nltk.tokenize import word_tokenize
from nltk.tokenize import sent_tokenize
from nltk.chunk import ne_chunk
from nltk.tree import *
from nltk.corpus import words
import nltk
import en
import sys, getopt

colors = ["red", "green", "blue", "cyan", "yellow", "magenta"]
color_map = {}
actual_verb_tags = ["VB", "VBD", "VBP", "VBZ"]
proper_noun_tags = ["NNP", "NNPS"]
noun_tags = proper_noun_tags + ["NN", "NNS", "PRP"]
subject_tags = noun_tags + ["DT", "WP$", "PRP$"]
punctuation = ".,?!;:()-"
word_set = set(words.words())
corpus = nltk.Text(word.lower() for word in word_set)
metric_sums = []
html_header = """
 <body>
  <div id="wrapper">
   <h1>Tribehacks | Logapps Challenge</h1>
   <link rel="stylesheet" href="logapps2.css">

   <table id="keywords" cellspacing="0" cellpadding="0">
     <thead>
       <tr>
         <th><span>Para. #</span></th>
         <th><span>Sent. #</span></th>
         <th><span>Subject</span></th>
         <th><span>Verbs</span></th>
         <th><span>Actual Verbs</span></th>
         <th><span>Remaining</span></th>
         <th><span>Ctg. #1</span></th>
         <th><span>Ctg. #2</span></th>
         <th><span>Ctg. #3</span></th>
         <th><span>Ctg. #4</span></th>
         <th><span>Ctg. #5</span></th>
         <th><span>Ctg. #6</span></th>
         <th><span>Ctg. #7</span></th>
       </tr>
     </thead>
     <tbody> """
html_footer = """</tbody></table></div>
<script src="https://d3js.org/d3.v3.min.js" charset="utf-8"></script>
<meta charset="utf-8">
<style>

.arc text {
  font: 10px sans-serif;
  text-anchor: middle;
}

.arc path {
  stroke: #fff;
}

</style>
<body>
<script>

var width = 960,
    height = 500,
    radius = Math.min(width, height) / 2;

var color = d3.scale.ordinal()
    .range(["#33FFFF", "#FF6666", "#7b6888", "#6b486b", "#a05d56", "#d0743c", "#ff8c00"]);

var arc = d3.svg.arc()
    .outerRadius(radius - 10)
    .innerRadius(0);

var labelArc = d3.svg.arc()
    .outerRadius(radius - 40)
    .innerRadius(radius - 40);

var pie = d3.layout.pie()
    .sort(null)
    .value(function(d) { return d.value; });

var svg = d3.select("body").append("svg")
    .attr("width", width)
    .attr("height", height)
  .append("g")
    .attr("transform", "translate(" + width / 2 + "," + height / 2 + ")");

d3.csv("logapps2.csv", type, function(error, data) {
  if (error) throw error;

  var g = svg.selectAll(".arc")
      .data(pie(data))
    .enter().append("g")
      .attr("class", "arc");

  g.append("path")
      .attr("d", arc)
      .style("fill", function(d) { return color(d.data.category); });

  g.append("text")
      .attr("transform", function(d) { return "translate(" + labelArc.centroid(d) + ")"; })
      .attr("dy", ".35em")
      .text(function(d) { return d.data.category; });
});

function type(d) {
  d.value = +d.value;
  return d;
}

</script></body>
"""


class RowData :
    """A RowData class stores the information relevant to each row in the table """

    def __init__(self, paragraph_count, sentence_count) :
        self.subjects = set()
        self.tokens = []
        self.verbs = set()
        self.actual_verbs = set()
        self.remaining = set()
        self.para = paragraph_count
        self.sent = sentence_count
        self.metrics = []


    def add_token(self, token) :
        self.tokens.append(token)


    def parse_tokens(self) :
        """ After all tokens have been added, this function may be called to
            filter relevant words into the verb, subject, and other sets"""
        i = 0
        while i < len(self.tokens) :
            #if the word is a verb, look for its subject
            if self.tokens[i][1] in actual_verb_tags :
                self.find_subject(i)
                try :
                    self.actual_verbs.add(en.verb.present(self.tokens[i][0]).capitalize())
                except KeyError :
                    #print("Error: " + self.tokens[i][0])
            #if the word is a gerund, check for a preceding verb
            elif 'V' in self.tokens[i][1] and self.tokens[i - 1][1] not in noun_tags :
                try :
                    self.actual_verbs.add(en.verb.present(self.tokens[i][0]).capitalize())
                except KeyError :
                    #print("Error: " + self.tokens[i][0])
            #if the gerund has no companion, it is not an 'actual' verb
            elif 'V' in self.tokens[i][1] :
                self.verbs.add(self.tokens[i][0].capitalize())
            #if the word is not punctuation or a verb, add it to remaining
            elif self.tokens[i][1] not in punctuation :
                self.remaining.add(self.tokens[i][0])
            i += 1

        #remove extraneous nouns from remaining list
        if len(self.actual_verbs) > 1 :
            self.actual_verbs.discard("Be")
        for subject in self.subjects :
            for word in subject.split() :
                self.remaining.discard(word)


    def __str__(self) :
        """ Prints the row to the terminal """
        line = "-" * 30
        string = line + "\n"
        string += "| " + str(self.para) + " | " + str(self.sent) + " | "
        for noun in self.subjects :
            string += noun + " "
        string += "| "
        for verb in (self.verbs.union(self.actual_verbs)) :
            string += verb + " "
        string += "| "
        for verb in self.actual_verbs :
            string += verb + " "
        string += "| "
        for word in self.remaining :
            string += word + " "
        for metric in self.metrics :
            string += metric + " | "
        string += "|"

        return string


    def find_subject(self, ndx) :
        """ Backtracks from the given index, looking for a noun or sequence thereof """
        subject = ""
        while ndx >= 0 :
            #if a noun is found first, begin recording the subject
            if self.tokens[ndx][1] in noun_tags :
                break
            #if punctuation encountered first, no subject can be found
            elif self.tokens[ndx][1] in punctuation :
                return
            ndx -= 1
        #Build the subject as a sequence of nouns in one string
        while ndx >= 0 and self.tokens[ndx][1] in subject_tags :
            subject = self.tokens[ndx][0] + " " + subject
            if self.tokens[ndx][1] not in noun_tags :
                break
            ndx -= 1
        self.subjects.add(subject)


    def isempty(self) :
        """isempty() returns true if nothing or only punctuation is present"""
        return len(self.subjects) + len(self.verbs) + len(self.actual_verbs) + len(self.remaining) == 0


    def apply_verb_metrics(self, metrics, ignore_list) :
        """ For a given metric mapping, calculate the values for this sentence,
            ignoring words in ignore_list """

        #Add relevant words to the ignore_list
        ignore_flag = 0
        for i in range(len(self.tokens)) :
            token = self.tokens[i]
            #ignore_flag is used to remember encountered brackets "[{("
            if ignore_flag < 0 :
                ignore_list += token[0]
            #Don't consider verbs similar to nouns in the sentence
            #if token[1] in noun_tags :
            #    similar_words = corpus.similar(token[0])
            #    if similar_words :
            #        ignore_list += similar_words
            #Do not count verbs contained within brackets
            if token[0] in "[{(" :
                ignore_flag -= 1
            if token[0] in "]})" :
                ignore_flag += 1


        self.metrics = ["" for val in list(metrics.values())[0]]
        sums = [0 for val in list(metrics.values())[0]]
        metric_list = []
        for verb in self.actual_verbs :
            if (verb.lower() not in ignore_list) and (verb.lower() in metrics) :
                metric_list.append(verb.lower())
                for i in range(len(metrics[verb.lower()])) :
                    self.metrics[i] += str(metrics[verb.lower()][i]) + "+\n"
                    sums[i] += int(metrics[verb.lower()][i])
            elif verb.lower() in metrics :
                for i in range(len(self.metrics)) :
                    self.metrics[i] += "0+\n"


        for i in range(len(self.metrics)) :
            self.metrics[i] = self.metrics[i][:len(self.metrics[i]) - 2] + "=" + str(sums[i])
            if self.metrics[i] == "=0" :
                self.metrics[i] = "0"

        for i in range(len(sums)) :
            metric_sums[i] += sums[i]

        return metric_list


    def to_html(self) :
        """ outputs this row as a table-row to html """
        html_string = "<tr>" + "<td>" + str(self.para) + "</td><td>" + str(self.sent) + "</td>\n"
        html_string += "<td>"
        for noun in self.subjects :
            html_string += noun + " "
        html_string += "</td> \n<td>"
        for verb in (self.verbs.union(self.actual_verbs)) :
            html_string += verb + " "
        html_string += "</td> \n<td>"
        for verb in self.actual_verbs :
            html_string += verb + " "
        html_string += "</td> \n<td>"
        for word in self.remaining :
            html_string += word + " "
        html_string += "</td>"
        for metric in self.metrics :
            html_string += "<td>" + metric + "</td>\n"
        html_string += "</tr>"
        return html_string




def remove_identifier(line) :
    """ removes outline/identifiers from the start of a line"""
    line_list = line.split()
    if len(line_list) > 0 and line_list[0].lower() not in word_set :
        return ". " +line[len(line_list[0]):]
    return line


def write_to_csv(row_list, file_name) :
    """ writes the row_list to the file using csv notation"""
    file_out = open(file_name, "w")
    for row in row_list :
        file_out.write(row.to_csv())
    file_out.close()


def write_to_html(row_list, file_name) :
    """ Writes the row_list to the file using html"""
    file_out = open(file_name, "w")
    file_out.write(html_header)
    for row in row_list :
        file_out.write(row.to_html())
    file_out.write(html_footer)
    file_out.close()


def get_paragraphs(file_name) :
    """ Separates an input file into a list of paragraphs, removing identifiers """
    file_input = open(file_name, "r")
    paragraphs = [" "]
    for line in file_input :
        line = line.strip("\n")
        line = remove_identifier(line)
        if line == "" :
            paragraphs.append("")
        paragraphs[-1] += line + " "
    file_input.close()
    return paragraphs


def get_rows(paragraph_list) :
    """ separates a list of paragraph strings into a list of RowData objects,
        parsing their tokens """
    paragraph_count = 0
    sentence_count = 1
    rows = []
    for paragraph in paragraph_list :
        paragraph = sent_tokenize(paragraph)
        paragraph_count += 1
        sentence_count = 1
        for sent in paragraph :
            row = RowData(paragraph_count, sentence_count)
            for token in pos_tag(word_tokenize(sent)) :
                row.add_token(token)
            row.parse_tokens()
            if not row.isempty() :
                rows.append(row)
                sentence_count += 1
    return rows


def get_metrics_from_file(file_name) :
    """ Reads in a metrics file of format datatype, {category_metrics}"""
    metrics = dict()
    file_input = open(file_name, "r")
    file_input.readline()
    for line in file_input :
        line = line.strip().split(",")
        metrics[line[0].lower().strip()] = line[1:]
    file_input.close()
    for i in range(len((metrics.values())[0])) :
        metric_sums.append(0)
    return metrics


def apply_metrics_to_row_data(metrics, row_list) :
    """ Calculate the sentence metrics for each row in the data set"""
    ignore_list = []
    paragraph = 1
    for row in row_list :
        if row.para != paragraph :
            paragraph = row.para
            ignore_list = []
        ignore_list = row.apply_verb_metrics(metrics, ignore_list)


def sentiment_analysis(row_list) :
    """Uses Minqing Hu and Bing Liu's opinion lexicon to determine the overall
        negative or positive tone of the input file """
    dictionary = {}
    pos_words = open("opinion-lexicon-English/positive-words.txt", "r")
    neg_words = open("opinion-lexicon-English/negative-words.txt", "r")
    for line in pos_words :
        word = line.strip()
        dictionary[word] = 0
    for line in neg_words :
        word = line.strip()
        dictionary[word] = 1

    pos_words.close()
    neg_words.close()

    score = [0, 0] #pos, neg
    neutral_score = 0
    for row in row_list :
        for token in row.tokens :
            if token[0] in dictionary :
                score[dictionary[token[0]]] += 1
            else :
                neutral_score += 1
    print("Pos: " + str(score[0]) + " |Neg: " + str(score[1]) + " |Neutral: " + str(neutral_score))
    file_out = open("logapps2.csv", "w")
    file_out.write("category,value\n")
    file_out.write("Positive," + str(score[0]) + "\n")
    file_out.write("Negative," + str(score[1]))
    file_out.close()


def output_sums(data_list, file_name) :
    file_out = open(file_name, "w")
    file_out.write("category,value\n")
    for i in range(len(data_list)) :
        file_out.write(str(i + 1) + "," + str(data_list[i]) + "\n")
    file_out.close()


input_file = "gps_data.txt"
opts, args = getopt.getopt(sys.argv[1:], 'i:')
for opt, arg in opts :
    if opt == '-i' :
        input_file = arg

paragraphs = get_paragraphs(input_file)
rows = get_rows(paragraphs)
word_metrics = get_metrics_from_file("logapps_table1.csv")
apply_metrics_to_row_data(word_metrics, rows)
sentiment_analysis(rows)
write_to_html(rows, "logapps.html")
output_sums(metric_sums, "logapps.csv")
